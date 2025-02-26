import os
import random
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from tqdm import tqdm

from indexer.indexer.env import env
from indexer.indexer.processing.factory import ComponentFactory
from indexer.indexer.processing.processor import BlockProcessor
from indexer.indexer.storage.handler import BlockHandler
from indexer.indexer.storage.local import LocalBlockHandler
from indexer.indexer.database.models.status import ProcessingStatus, BlockProcess
from indexer.indexer.utils.logging import setup_logger
from indexer.indexer.decoders.block import BlockDecoder



class BatchProcessor:
    """
    Process batches of blocks with flexible storage options.
    """
    
    def __init__(self, storage_type="gcs", local_dir=None):
        """
        Initialize batch processor.
        
        Args:
            storage_type: Where to store decoded blocks ("gcs" or "local")
            local_dir: Local directory for storage if storage_type is "local"
        """
        self.logger = setup_logger(__name__)
        self.storage_type = storage_type
        self.local_dir = local_dir or env.get_path("data_dir")
        
        # Initialize components
        self.gcs_handler = ComponentFactory.get_gcs_handler()
        self.db_manager = ComponentFactory.get_database_manager()
        self.validator = ComponentFactory.get_block_validator()
        self.registry = ComponentFactory.get_contract_registry()
        self.decoder = BlockDecoder(self.registry)
        
        if storage_type == "local":
            self.handler = LocalBlockHandler(
                gcs_handler=self.gcs_handler,
                local_dir=local_dir,
                raw_prefix=env.get_rpc_prefix(),
                decoded_prefix=env.get_decoded_prefix()
            )
        else:
            self.handler = BlockHandler(
                gcs_handler=self.gcs_handler,
                raw_prefix=env.get_rpc_prefix(),
                decoded_prefix=env.get_decoded_prefix()
            )
        
        self.processor = BlockProcessor(
            gcs_handler=self.gcs_handler,
            status_tracker=self.db_manager,
            validator=self.validator,
            decoder=self.decoder,
            handler=self.handler
        )
    
    def list_available_blocks(self, prefix=None, max_blocks=1000) -> List[str]:
        """
        List available blocks from GCS.
        
        Returns:
            List of block paths
        """
        prefix = prefix or env.get_rpc_prefix()
        self.logger.info(f"Listing blocks in GCS bucket {self.gcs_handler.bucket_name} with prefix {prefix}...")
        
        blobs = list(self.gcs_handler.list_blobs(prefix=prefix))
        if max_blocks and len(blobs) > max_blocks:
            blobs = blobs[:max_blocks]
            
        return [blob.name for blob in blobs]
    
    def sample_blocks(self, count: int, prefix=None) -> List[str]:
        """
        Sample random blocks from available blocks.
        
        Returns:
            List of sampled block paths
        """
        available_blocks = self.list_available_blocks(prefix)
        
        if not available_blocks:
            self.logger.warning(f"No blocks found with prefix {prefix}")
            return []
        
        self.logger.info(f"Found {len(available_blocks)} blocks. Sampling {count}...")
        
        if len(available_blocks) <= count:
            return available_blocks
        else:
            return random.sample(available_blocks, count)
    
    def get_blocks_by_block_numbers(self, block_numbers: List[int], prefix=None) -> List[str]:
        """
        Get block paths by block numbers.
            
        Returns:
            List of block paths
        """
        prefix = prefix or env.get_rpc_prefix()
        
        block_paths = []
        for block_number in block_numbers:
            path = f"{prefix}{self.handler.build_path_from_block(block_number)}"

            if self.gcs_handler.blob_exists(path):
                block_paths.append(path)
            else:
                self.logger.warning(f"Block {block_number} not found at {path}")
        
        return block_paths
    
    def get_blocks_by_status(self, status: ProcessingStatus, limit: int = 100) -> List[str]:
        """
        Get blocks by processing status.
        
        Args:
            status: Processing status to filter by
            limit: Maximum number of blocks to retrieve
            
        Returns:
            List of block paths
        """
        blocks = self.db_manager.get_blocks_by_status(status, limit=limit)
        return [block.gcs_path for block in blocks]

    def get_blocks_in_range(self, min_block: int, max_block: int, status: Optional[ProcessingStatus] = None, prefix=None) -> List[str]:
        """
        Get blocks within a specified block number range, optionally filtered by status.
        
        Args:
            min_block: Minimum block number (inclusive)
            max_block: Maximum block number (inclusive)
            status: Optional filter by processing status
            prefix: GCS prefix
            
        Returns:
            List of block paths
        """
        prefix = prefix or env.get_rpc_prefix()
        self.logger.info(f"Getting blocks in range {min_block} to {max_block}" + 
                        (f" with status {status.value}" if status else ""))
        
        # If status is provided, query database for blocks in range with that status
        if status:
            with self.db_manager.db.get_session() as session:
                blocks = session.query(BlockProcess).filter(
                    BlockProcess.block_number >= min_block,
                    BlockProcess.block_number <= max_block
                )
                
                if status:
                    blocks = blocks.filter(BlockProcess.status == status)
                    
                blocks = blocks.order_by(BlockProcess.block_number).all()
                
                # Return GCS paths
                return [block.gcs_path for block in blocks]
        
        # If no status filter, try to get blocks directly from GCS
        # This is more efficient when we don't need to filter by status
        else:
            block_paths = []
            for block_number in range(min_block, max_block + 1):
                path = f"{prefix}{self.handler.build_path_from_block(block_number)}"
                if self.gcs_handler.blob_exists(path):
                    block_paths.append(path)
            
            return block_paths
    
    def process_blocks(self, block_paths: List[str]) -> Dict[str, Any]:
        """
        Process a batch of blocks.
        
        Args:
            block_paths: List of block paths to process
            
        Returns:
            Processing results
        """
        results = {
            "total": len(block_paths),
            "success": 0,
            "failure": 0,
            "started_at": datetime.now().isoformat(),
            "details": []
        }
        
        if not block_paths:
            self.logger.warning("No blocks to process")
            return results
        
        self.logger.info(f"Processing {len(block_paths)} blocks...")
        
        for path in tqdm(block_paths, desc="Processing blocks"):
            try:
                success, result_info = self.processor.process_block(path)
                
                if success:
                    results["success"] += 1
                else:
                    results["failure"] += 1
                    
                results["details"].append({
                    "path": path,
                    "success": success,
                    "info": result_info
                })
            except Exception as e:
                self.logger.error(f"Error processing {path}: {str(e)}")
                results["failure"] += 1
                results["details"].append({
                    "path": path,
                    "success": False,
                    "error": str(e)
                })
        
        results["ended_at"] = datetime.now().isoformat()
        results["duration_seconds"] = (
            datetime.fromisoformat(results["ended_at"]) - 
            datetime.fromisoformat(results["started_at"])
        ).total_seconds()
        
        self.logger.info(f"Processing complete: {results['success']} successful, {results['failure']} failed")
        return results
    
    def save_results(self, results: Dict[str, Any], output_file: Optional[str] = None) -> str:
        """
        Save processing results to file.
        
        Args:
            results: Processing results
            output_file: Output file path (default: auto-generated)
            
        Returns:
            Path to saved results file
        """
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.storage_type == "local":
                output_dir = Path(self.local_dir or env.get_path('data_dir'))
            else:
                output_dir = env.get_path('data_dir')
            
            output_file = output_dir / f"batch_results_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Results saved to {output_file}")
        return str(output_file)