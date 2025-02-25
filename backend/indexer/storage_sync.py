import os
from pathlib import Path
from dotenv import load_dotenv

from backend.indexer.indexer.storage.base import GCSHandler
from indexer.indexer.storage.sync import GCSLocalSync
from indexer.indexer.storage.manager import RPCLocalCopy


def main():
    print("entered main")
    load_dotenv()
    
    local_dir = Path(__file__).parent.parent / os.getenv("LOCAL_RPC_DIR")
    print(local_dir.resolve())
    

    '''
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
    GCS_CREDENTIALS_PATH = os.getenv("GCS_CREDENTIALS_PATH")
    GCS_RPC_PREFIX = os.getenv("GCS_RPC_PREFIX")

    gcs_handler = GCSHandler(GCS_BUCKET_NAME, GCS_CREDENTIALS_PATH)
    sync = RPCLocalCopy(gcs_handler, local_dir)
    
    print("\n=== Regular Sync ===")
    stats = sync.sync(prefix=GCS_RPC_PREFIX)
    print(f"Sync statistics: {stats}")
    '''

print("before if")
if __name__ == "__storage_sync__":
    print("entered if")
    main()