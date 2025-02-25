from typing import Tuple, Optional, Dict, Any, List
import json

from indexer.indexer.env import env
from indexer.indexer.storage.base import GCSBaseHandler

class BlockHandler():
    def __init__(self,gcs_handler: GCSBaseHandler,
                 raw_prefix: str = None,
                 decoded_prefix: str = None):
        self.gcs_handler = gcs_handler
        self.raw_prefix = raw_prefix or env.get_rpc_prefix()
        self.decoded_prefix = decoded_prefix or env.get_decoded_prefix()

    def extract_block_number(self, gcs_path: str) -> int:
        """Extract block number from GCS path."""
        block_num = gcs_path.split('-')[-1].split('.')[0]
        return int(block_num.lstrip('0'))

    def store_decoded_block(self, block_number: int, decoded_data: Dict[str, Any]) -> bool:
        """
        Store decoded block data in GCS.
            
        Returns:
            True if storage was successful
        """
        destination = f"{self.decoded_prefix}block_{block_number}.json"
        return self.gcs_handler.upload_blob_from_string(
            json.dumps(decoded_data), 
            destination,
            content_type="application/json"
        )
    
    def get_raw_block(self, block_number: int) -> Optional[bytes]:
        """
        Retrieve raw block data from GCS.
            
        Returns:
            Raw block data if found, None otherwise
        """
        path = f"{self.raw_prefix}block_{block_number}.json"
        return self.gcs_handler.download_blob_as_bytes(path)
    
    def get_decoded_block(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve decoded block data from GCS.
            
        Returns:
            Decoded block data if found, None otherwise
        """
        path = f"{self.decoded_prefix}block_{block_number}.json"
        data = self.gcs_handler.download_blob_as_text(path)
        if data:
            return json.loads(data)
        return None