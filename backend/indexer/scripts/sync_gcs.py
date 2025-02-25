"""
Development script to sync GCS data.
"""

import os
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[1]))

from indexer.env import paths
from indexer.storage.sync import GCSLocalSync
from backend.indexer.indexer.storage.base import GCSHandler


class RPCBlockCopy(GCSLocalSync):    

    def rename_file(self, gcs_path: str) -> str:
        """Custom renaming logic that transforms GCS paths to local paths."""

        split = gcs_path.split('-')[-1]
        filename = split.lstrip('0')        

        return os.path.join(self.local_dir, filename)


def main():
    print(f"Syncing data to: {paths['rpc_dir']}")
    handler = GCSHandler(os.getenv('GCS_BUCKET_NAME'))
    syncer = RPCBlockCopy(handler,os.getenv('LOCAL_RPC_BLOCKS_DIR'))
    syncer.sync(os.getenv('GCS_RPC_PREFIX'))
    print("Sync complete")


if __name__ == "__main__":
    main()