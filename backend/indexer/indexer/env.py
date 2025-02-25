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
            'GCS_BUCKET_NAME',
            'GCS_PROJECT_ID',
            'AVAX_RPC'
        ]
        
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
        
        if not all([db_user, db_pass, db_name, db_host]):
            # Development fallback - SQLite
            data_dir = self.paths['data_dir']
            return f"sqlite:///{data_dir}/dev.db"
        
        return f"postgresql://{db_user}:{db_pass}@{db_host}/{db_name}"

    def get_bucket_name(self):
        return os.getenv("GCS_BUCKET_NAME")

    def get_project_id(self):
        return os.getenv("GCS_PROJECT_ID")

    def get_rpc_url(self):
        return os.getenv("AVAX_RPC")

    def get_gcs_prefix(self):
        return os.getenv("GCS_RPC_PREFIX", "")


env = IndexerEnvironment()