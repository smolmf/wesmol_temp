
import json
from pathlib import Path

from ..env import env
from .handler import BlockHandler
from ..utils.logging import setup_logger

class LocalBlockHandler(BlockHandler):
    """Extension of BlockHandler that stores decoded blocks locally."""
    
    def __init__(self, gcs_handler, local_dir=None, raw_prefix=None, decoded_prefix=None):
        super().__init__(gcs_handler, raw_prefix, decoded_prefix)
        self.local_dir = Path(local_dir or env.get_path('data_dir'))
        self.local_decoded_dir = self.local_dir / "decoded"
        self.local_decoded_dir.mkdir(parents=True, exist_ok=True)
        self.logger = setup_logger(__name__)
        
    def store_decoded_block(self, block_number: int, decoded_data):
        """Store decoded block data to local filesystem."""
        try:
            file_path = self.local_decoded_dir / f"{block_number}.json"
            self.logger.info(f"Storing decoded block {block_number} to {file_path}")
            
            with open(file_path, 'w') as f:
                json.dump(decoded_data, f, default=self._json_serializer, indent=2)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to store decoded block {block_number}: {str(e)}")
            return False
        
    def decoded_block_exists(self, block_number: int) -> bool:
        file_path = self.local_decoded_dir / f"{block_number}.json"
        return file_path.exists()
    
    def _json_serializer(self, obj):
        """Custom JSON serializer for objects not serializable by default json code"""
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        raise TypeError(f"Type {type(obj)} not serializable")