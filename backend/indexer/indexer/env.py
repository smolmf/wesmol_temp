import os
from pathlib import Path
from dotenv import load_dotenv

class IndexerEnvironment:
    def __init__(self):
        self.current_dir = Path(__file__).resolve()
        self.indexer_root = self.current_dir.parents[1]  # wesmol/backend/indexer
        self.project_root = self.indexer_root.parents[1]  # project root (wesmol)

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
    
    def _validate_env(self):
        required_vars = [
            "GCS_PROJECT_ID",
            "GCS_BUCKET_NAME",
            "GCS_CREDENTIALS_PATH",
            "GCS_RPC_PREFIX",
            "GCS_DECODED_PREFIX",
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

    def get_path(self, name):
        return self.paths.get(name)

    def get_db_url(self):
        db_user = os.getenv("DB_USER")
        db_pass = os.getenv("DB_PASS")
        db_name = os.getenv("DB_NAME")
        db_host = os.getenv("DB_HOST")
        db_port = os.getenv("DB_PORT")
        
        if not all([db_user, db_pass, db_name, db_host]):
            # Development fallback - SQLite
            data_dir = self.paths['data_dir']
            return f"sqlite:///{data_dir}/dev.db"
        
        return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"

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
    
env = IndexerEnvironment()