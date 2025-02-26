import os
import re
import logging
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

class IndexerEnvironment:
    def __init__(self):
        self.current_dir = Path(__file__).resolve()
        self.indexer_root = self.current_dir.parents[1]  # wesmol/backend/indexer
        self.project_root = self.indexer_root.parents[1]  # project root (wesmol)

        # Initialize logger
        self.logger = logging.getLogger("indexer.env")

        # Initialize paths
        self.paths = {
            'project_root': self.project_root,
            'indexer_root': self.indexer_root,
            'data_dir': self.project_root / 'data',
            'config_dir': self.indexer_root / 'config'
        }

        for path in self.paths.values():
            path.mkdir(parents=True, exist_ok=True)

        load_dotenv(self.project_root / '.env')       # Load project-wide vars FIRST
        load_dotenv(self.indexer_root / '.env')       # THEN Load indexer-specific vars
        
        self._validate_env()

        # Initialize database connection if validation passes
        self.db_engine = None
        if self._validate_db_config():
            self._init_db_connection()
    
    def _validate_env(self):
        required_vars = [
            "ENVIRONMENT",
            "LOG_LEVEL",
            "DB_USE_SQLITE",
            "GCS_PROJECT_ID",
            "GCS_BUCKET_NAME",
            "GCS_CREDENTIALS_PATH",
            "GCS_RPC_PREFIX",
            "GCS_DECODED_PREFIX",
            "RAW_BLOCK_FORMAT",
            "DECODED_BLOCK_FORMAT",
            "RPC_BLOCK_FORMAT",
            "AVAX_RPC",
            "PORT"
        ]

        db_vars = ['DB_USER', 'DB_PASS', 'DB_NAME', 'DB_HOST', 'DB_PORT']
        db_present = [var for var in db_vars if os.getenv(var)]

        if 0 < len(db_present) < len(db_vars):
            missing_db = [var for var in db_vars if not os.getenv(var)]
            raise ValueError(f"Incomplete database configuration. Missing: {', '.join(missing_db)}")
        
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    def _validate_db_config(self):
        """Validate database configuration."""
        # Check for explicit SQLite setting
        if os.getenv("DB_USE_SQLITE", "").lower() in ("true", "1", "yes"):
            self.logger.info("Using SQLite database (explicitly configured)")
            return True
        
        # Check PostgreSQL config
        db_vars = ['DB_USER', 'DB_PASS', 'DB_NAME', 'DB_HOST']
        db_present = [var for var in db_vars if os.getenv(var)]
        
        if len(db_present) == 0:
            # No DB config provided, will use SQLite default
            self.logger.info("No database configuration found, will use SQLite")
            return True
        elif len(db_present) < len(db_vars):
            # Incomplete PostgreSQL config
            missing_db = [var for var in db_vars if not os.getenv(var)]
            self.logger.warning(f"Incomplete database configuration. Missing: {', '.join(missing_db)}")
            self.logger.warning("Falling back to SQLite database")
            return True
        
        # Complete PostgreSQL config
        self.logger.info("Using PostgreSQL database")
        return True

    def _init_db_connection(self):
        """Initialize database connection and verify it works."""
        db_url = self.get_db_url()
        # Mask password in logs
        masked_url = db_url
        if ":" in db_url and "@" in db_url:
            parts = db_url.split(":")
            if len(parts) > 2:
                masked_url = f"{parts[0]}:{parts[1]}:****@{db_url.split('@')[1]}"
        
        self.logger.info(f"Initializing database connection to {masked_url}")
        
        try:
            # Create engine with reasonable defaults
            self.db_engine = create_engine(
                db_url,
                pool_pre_ping=True,  # Verify connection before using
                pool_recycle=300,    # Recycle connections after 5 minutes
                pool_size=5,         # Maintain a pool of 5 connections
                max_overflow=10      # Allow up to 10 additional connections
            )
            
            # Test connection
            with self.db_engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                if result == 1:
                    self.logger.info("Database connection verified")
                    return True
                else:
                    self.logger.warning("Database connection test returned unexpected result")
                    return False
        except SQLAlchemyError as e:
            self.logger.error(f"Database connection failed: {str(e)}")
            self.logger.warning("Application may not function correctly without database access")
            self.db_engine = None
            return False

    def get_path(self, name):
        return self.paths.get(name)

    def is_development(self):
        return os.getenv("ENVIRONMENT", "").lower() == "development"

    def get_log_level(self):
        """Get configured log level."""
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        return level if level in valid_levels else "INFO"

    def get_db_url(self):
        """Get database connection URL from environment."""
        # Check for explicit SQLite override
        if os.getenv("DB_USE_SQLITE", "").lower() in ("true", "1", "yes"):
            # Use SQLite for local development
            data_dir = self.paths['data_dir']
            return f"sqlite:///{data_dir}/wesmol.db"
        
        # PostgreSQL connection
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASS")
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT", "5432")
        
        if not all([db_user, db_pass, db_name, db_host]):
            # Development fallback - SQLite
            data_dir = self.paths['data_dir']
            return f"sqlite:///{data_dir}/wesmol.db"
        
        return f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"

    def verify_database(self):
        """
        Verify database connection and schema.
        Returns True if database is ready, False otherwise.
        """
        if not self.db_engine:
            success = self._init_db_connection()
            if not success:
                return False
        
        try:
            # Check if key tables exist by trying a simple query
            from indexer.indexer.database.models.status import BlockProcess
            with self.db_engine.connect() as conn:
                # Try to access the BlockProcess table
                result = conn.execute(text(f"SELECT 1 FROM {BlockProcess.__tablename__} LIMIT 1"))
                # Just checking if the query works, don't need the result
                list(result)
                self.logger.info("Database schema verification successful")
                return True
        except Exception as e:
            self.logger.warning(f"Database schema verification failed: {str(e)}")
            self.logger.info("Tables may need to be created. Running initialization...")
            
            try:
                # Import and create tables
                from indexer.indexer.database.models.base import Base
                Base.metadata.create_all(self.db_engine)
                self.logger.info("Database tables created successfully")
                return True
            except Exception as e:
                self.logger.error(f"Failed to create database tables: {str(e)}")
                return False
            
    def get_db_engine(self):
        """Get SQLAlchemy engine instance."""
        if not self.db_engine:
            self._init_db_connection()
        return self.db_engine

    def get_gcs_credentials(self):
        return os.getenv("GCS_CREDENTIALS_PATH")

    def get_bucket_name(self):
        return os.getenv("GCS_BUCKET_NAME")

    def get_project_id(self):
        return os.getenv("GCS_PROJECT_ID")

    def get_rpc_url(self):
        return os.getenv("AVAX_RPC")

    def get_rpc_prefix(self):
        return os.getenv("GCS_RPC_PREFIX")
    
    def get_decoded_prefix(self):
        return os.getenv("GCS_DECODED_PREFIX")

    def get_service_port(self):
        return os.getenv("PORT")
    
    def get_rpc_block_path_format(self):
        return os.getenv("RPC_BLOCK_FORMAT", "{}.json")

    def get_raw_block_path_format(self):
        return os.getenv("RAW_BLOCK_FORMAT", "{}.json")

    def get_decoded_block_path_format(self):
        """Get format string for decoded block paths."""
        return os.getenv("DECODED_BLOCK_FORMAT", "{}.json")

    def format_rpc_block_path(self, block_number):
        """Format a raw block path with the given block number."""
        format_str = self.get_rpc_block_path_format()

        # Check if the format has multiple placeholders (for quicknode format)
        if format_str.count('{}') > 1 or '{:' in format_str:
            # For quicknode format with padding, pass the same block number twice
            return f"{self.get_rpc_prefix()}{format_str.format(block_number, block_number)}"
        else:
            # For standard format
            return f"{self.get_rpc_prefix()}{format_str.format(block_number)}"

    def format_raw_block_path(self, block_number):
        """Format a raw block path with the given block number."""
        format_str = self.get_raw_block_path_format()
        return f"{self.get_rpc_prefix()}{format_str.format(block_number)}"

    def format_decoded_block_path(self, block_number):
        """Format a decoded block path with the given block number."""
        format_str = self.get_decoded_block_path_format()
        return f"{self.get_decoded_prefix()}{format_str.format(block_number)}"

    def extract_block_number(self, path):
        """
        Extract block number from a block path.
        
        This handles different path formats based on their prefixes.
        """
        # Get prefixes for comparison
        raw_prefix = self.get_rpc_prefix()
        decoded_prefix = self.get_decoded_prefix()
        
        try:
            if path.startswith(raw_prefix):
                # Handle raw block format
                # Try standard format first
                filename = path[len(raw_prefix):]
                format_str = self.get_raw_block_path_format()
                
                # Convert format string to regex pattern
                # Replace {} with capture group for digits
                pattern = format_str.replace(".", "\\.").replace("{}", "([0-9]+)")
                match = re.search(pattern, filename)
                
                if match:
                    return int(match.group(1))
                    
                # Try quicknode format as fallback
                if "quicknode" in path:
                    # Example: quicknode_avalanche-mainnet_block_with_receipts_00012345-00012345.json
                    parts = filename.split('_')
                    if len(parts) >= 5:
                        number_part = parts[-1].split('.')[0]  # Get "00012345-00012345"
                        return int(number_part.split('-')[0])  # Get first number and convert
                        
            elif path.startswith(decoded_prefix):
                # Handle decoded block format
                filename = path[len(decoded_prefix):]
                format_str = self.get_decoded_block_path_format()
                
                # Convert format string to regex pattern
                pattern = format_str.replace(".", "\\.").replace("{}", "([0-9]+)")
                match = re.search(pattern, filename)
                
                if match:
                    return int(match.group(1))
            
            # Generic extraction for simple patterns
            # Try to find block_NUMBER.json pattern
            match = re.search(r"block_([0-9]+)\.json", path)
            if match:
                return int(match.group(1))
                
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to extract block number from {path}: {e}")
        
        raise ValueError(f"Could not extract block number from path: {path}")
    
env = IndexerEnvironment()