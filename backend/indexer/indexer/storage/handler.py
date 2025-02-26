from typing import Tuple, Optional, Dict, Any, List
import json

from ..env import env
from ..utils.logging import setup_logger
from .base import GCSBaseHandler

class BlockHandler():
    def __init__(self,gcs_handler: GCSBaseHandler,
                 raw_prefix: str = None,
                 decoded_prefix: str = None):
        self.gcs_handler = gcs_handler
        self.raw_prefix = raw_prefix or env.get_rpc_prefix()
        self.decoded_prefix = decoded_prefix or env.get_decoded_prefix()
        self.logger = setup_logger(__name__)

    def extract_block_number(self, gcs_path: str) -> int:
        """Extract block number from GCS path."""
        return env.extract_block_number(gcs_path)
    
    def build_path_from_block(self, block_number: int) -> str:
        padded_number = str(block_number).zfill(12)
        return f"quicknode_avalanche-mainnet_block_with_receipts_{padded_number}-{padded_number}.json"

    def store_decoded_block(self, block_number: int, decoded_data: Dict[str, Any]) -> bool:
        """
        Store decoded block data in GCS.
            
        Returns:
            True if storage was successful
        """
        destination = f"{self.decoded_prefix}{block_number}.json"
        return self.gcs_handler.upload_blob_from_string(
            json.dumps(decoded_data), 
            destination,
            content_type="application/json"
        )
    
    def get_raw_block_path(self, block_number: int) -> str:
        """Generate path for raw block file."""
        return env.format_raw_block_path(block_number)
    
    def get_decoded_block_path(self, block_number: int) -> str:
        """Generate path for decoded block file."""
        return env.format_decoded_block_path(block_number)
    
    def get_raw_block(self, block_number: int) -> Optional[bytes]:
        """
        Retrieve raw block data from GCS.
            
        Returns:
            Raw block data if found, None otherwise
        """
        path = f"{self.raw_prefix}{self.build_path_from_block(block_number)}"
        return self.gcs_handler.download_blob_as_bytes(path)
    
    def get_decoded_block(self, block_number: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve decoded block data from GCS.
            
        Returns:
            Decoded block data if found, None otherwise
        """
        path = f"{self.decoded_prefix}{block_number}.json"
        data = self.gcs_handler.download_blob_as_text(path)
        if data:
            return json.loads(data)
        return None
    
    def decoded_block_exists(self, block_number: int) -> bool:
        path = f"{self.decoded_prefix}{block_number}.json"
        return self.gcs_handler.blob_exists(path)