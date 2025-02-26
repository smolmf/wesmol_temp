import os
import time
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
    
    def __init__(self, storage_type="gcs", local_dir=None, use_local_db=False):
        """
        Initialize batch processor.
        
        Args:
            storage_type: Where to store decoded blocks ("gcs" or "local")
            local_dir: Local directory for storage if storage_type is "local"
            use_local_db: Whether to use local SQLite database
        """
        self.logger = setup_logger(__name__)
        self.storage_type = storage_type
        self.local_dir = local_dir
        
        # Force use of SQLite for local development if requested
        if use_local_db:
            os.environ["DB_USE_SQLITE"] = "True"
            self.logger.info("Using local SQLite database")
        
        # Initialize components
        self.gcs_handler = ComponentFactory.get_gcs_handler()
        self.db_manager = ComponentFactory.get_database_manager()
        self.validator = ComponentFactory.get_block_validator()
        self.registry = ComponentFactory.get_contract_registry()
        
        # Create decoder
        self.decoder = BlockDecoder(self.registry)
        
        # Create appropriate handler
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
        
        # Create block processor
        self.processor = BlockProcessor(
            gcs_handler=self.gcs_handler,
            status_tracker=self.db_manager,
            validator=self.validator,
            decoder=self.decoder,
            handler=self.handler
        )
    
    def list_available_blocks(self, prefix=None, max_blocks=1000, sync_first=True) -> List[str]:
        """
        List available blocks from database (syncing from GCS first if requested).
        
        Args:
            prefix: GCS prefix to filter by
            max_blocks: Maximum number of blocks to list
            sync_first: Whether to sync GCS objects to database first
                
        Returns:
            List of block paths
        """
        file_type = 'raw'
        if prefix and 'decoded/' in prefix:
            file_type = 'decoded'
        
        if sync_first:
            # Sync GCS objects to database
            self.logger.info(f"Syncing {file_type} GCS objects to database...")
            count = self.db_manager.sync_gcs_objects(prefix=prefix)
            self.logger.info(f"Synced {count} GCS objects to database")
        
        # Get paths from database
        paths = self.db_manager.get_available_block_paths(file_type=file_type, limit=max_blocks)
        self.logger.info(f"Found {len(paths)} blocks in database")
        
        return paths
    
    def sample_blocks(self, count: int, prefix=None, sync_first=True) -> List[str]:
        """
        Sample random blocks from available blocks.
        
        Args:
            count: Number of blocks to sample
            prefix: GCS prefix to sample from
            sync_first: Whether to sync GCS objects to database first
            
        Returns:
            List of sampled block paths
        """
        available_blocks = self.list_available_blocks(prefix, sync_first=sync_first)
        
        if not available_blocks:
            self.logger.warning(f"No blocks found with prefix {prefix}")
            return []
        
        self.logger.info(f"Found {len(available_blocks)} blocks. Sampling {count}...")
        
        if len(available_blocks) <= count:
            return available_blocks
        else:
            return random.sample(available_blocks, count)
    
    def get_blocks_by_block_numbers(self, block_numbers: List[int], prefix=None, sync_first=True) -> List[str]:
        """
        Get block paths by block numbers.
        
        Args:
            block_numbers: List of block numbers
            prefix: GCS prefix
            sync_first: Whether to sync GCS objects to database first
            
        Returns:
            List of block paths
        """
        prefix = prefix or env.get_rpc_prefix()
        file_type = 'raw'
        if 'decoded/' in prefix:
            file_type = 'decoded'
        
        if sync_first:
            # Sync GCS objects to database
            self.logger.info(f"Syncing {file_type} GCS objects to database...")
            count = self.db_manager.sync_gcs_objects(prefix=prefix)
            self.logger.info(f"Synced {count} GCS objects to database")
        
        # Get blocks from database
        block_paths = []
        for block_number in block_numbers:
            if self.db_manager.block_exists_in_gcs(block_number, file_type):
                if file_type == 'raw':
                    block_paths.append(env.format_raw_block_path(block_number))
                else:
                    block_paths.append(env.format_decoded_block_path(block_number))
            else:
                self.logger.warning(f"Block {block_number} not found in database")
        
        return block_paths
    
    def get_blocks_by_status(self, status: ProcessingStatus, limit: int = 100, sync_first=True) -> List[str]:
        """
        Get blocks by processing status.
        
        Args:
            status: Processing status to filter by
            limit: Maximum number of blocks to retrieve
            sync_first: Whether to sync GCS objects to database first
            
        Returns:
            List of block paths
        """
        if sync_first:
            # Sync GCS objects to database
            self.logger.info("Syncing GCS objects to database...")
            count = self.db_manager.sync_gcs_objects(prefix=env.get_rpc_prefix())
            self.logger.info(f"Synced {count} GCS objects to database")
        
        # Get blocks from database
        blocks = self.db_manager.get_blocks_by_status(status, limit=limit)
        
        # Convert to paths
        paths = []
        for block in blocks:
            # If gcs_path is stored, use it directly
            if hasattr(block, 'gcs_path') and block.gcs_path:
                paths.append(block.gcs_path)
            # Otherwise generate path from block number
            else:
                paths.append(env.format_raw_block_path(block.block_number))
        
        return paths
    
    def get_blocks_in_range(self, min_block: int, max_block: int, status: Optional[ProcessingStatus] = None, prefix=None, sync_first=True) -> List[str]:
        """
        Get blocks within a specified block number range, optionally filtered by status.
        
        Args:
            min_block: Minimum block number (inclusive)
            max_block: Maximum block number (inclusive)
            status: Optional filter by processing status
            prefix: GCS prefix
            sync_first: Whether to sync GCS objects to database first
            
        Returns:
            List of block paths
        """
        prefix = prefix or env.get_rpc_prefix()
        self.logger.info(f"Getting blocks in range {min_block} to {max_block}" + 
                        (f" with status {status.value}" if status else ""))
        
        file_type = 'raw'
        if 'decoded/' in prefix:
            file_type = 'decoded'
        
        if sync_first:
            # Sync GCS objects to database
            self.logger.info(f"Syncing {file_type} GCS objects to database...")
            count = self.db_manager.sync_gcs_objects(prefix=prefix)
            self.logger.info(f"Synced {count} GCS objects to database")
        
        # If status is provided, query database for blocks in range with that status
        if status:
            with self.db_manager.db.get_session() as session:
                blocks = session.query(BlockProcess).filter(
                    BlockProcess.block_number >= min_block,
                    BlockProcess.block_number <= max_block
                )
                
                blocks = blocks.filter(BlockProcess.status == status)
                blocks = blocks.order_by(BlockProcess.block_number).all()
                
                # Return GCS paths
                return [block.gcs_path for block in blocks if block.gcs_path]
        
        # If no status filter, get blocks directly from GCS objects table
        else:
            return self.db_manager.get_available_block_paths(
                file_type=file_type,
                min_block=min_block,
                max_block=max_block
            )
    
    def process_blocks(self, block_paths: List[str], batch_size: int = None, force: bool = False, sync_first: bool = True) -> Dict[str, Any]:
        """
        Process a batch of blocks, optionally breaking into smaller batches.
        
        Args:
            block_paths: List of block paths to process
            batch_size: Maximum number of blocks to process in a single batch
                       (None = process all at once)
            force: Force reprocessing even if decoded blocks already exist
            sync_first: Whether to sync GCS objects to database first
            
        Returns:
            Processing results
        """
        results = {
            "total": len(block_paths),
            "success": 0,
            "failure": 0,
            "skipped": 0,
            "started_at": datetime.now().isoformat(),
            "batches": [],
            "details": []
        }
        
        if not block_paths:
            self.logger.warning("No blocks to process")
            return results
        
        # Sync database if requested
        if sync_first:
            # Update database to know about decoded blocks
            self.logger.info("Updating GCS object database...")
            self.db_manager.sync_gcs_objects(prefix=env.get_decoded_prefix(), batch_size=1000)
        
        # Calculate batches
        if batch_size and batch_size < len(block_paths):
            batches = [block_paths[i:i + batch_size] for i in range(0, len(block_paths), batch_size)]
            self.logger.info(f"Processing {len(block_paths)} blocks in {len(batches)} batches of up to {batch_size} blocks each")
        else:
            batches = [block_paths]
            self.logger.info(f"Processing {len(block_paths)} blocks in a single batch")
        
        # Process each batch
        for batch_index, batch in enumerate(batches):
            batch_start_time = datetime.now()
            self.logger.info(f"Processing batch {batch_index + 1}/{len(batches)} with {len(batch)} blocks")
            
            batch_results = {
                "batch_index": batch_index + 1,
                "batch_size": len(batch),
                "success": 0,
                "failure": 0,
                "skipped": 0,
                "started_at": batch_start_time.isoformat(),
                "blocks": []
            }
            
            # Process each block with progress bar and periodic status updates
            total_blocks = len(batch)
            status_interval = max(1, min(100, total_blocks // 10))  # Update every ~10% of batch
            last_status_time = time.time()
            status_update_interval = 60  # Status update every minute for long batches
            
            with tqdm(total=total_blocks, desc=f"Batch {batch_index + 1}/{len(batches)}") as progress:
                for i, path in enumerate(batch):
                    try:
                        # Extract block number
                        block_number = env.extract_block_number(path)
                        
                        # Check if decoded block already exists (if not forcing)
                        skip_processing = False
                        if not force:
                            decoded_exists = False
                            
                            # Check database first
                            if self.db_manager.block_exists_in_gcs(block_number, 'decoded'):
                                decoded_exists = True
                            # Fallback to direct check if database might not be up to date
                            elif hasattr(self.handler, 'decoded_block_exists'):
                                if self.handler.decoded_block_exists(block_number):
                                    decoded_exists = True
                            
                            if decoded_exists:
                                self.logger.debug(f"Block {block_number} already decoded, skipping")
                                skip_processing = True
                                results["skipped"] += 1
                                batch_results["skipped"] += 1
                                
                                block_result = {
                                    "path": path,
                                    "block_number": block_number,
                                    "success": True,
                                    "skipped": True,
                                    "reason": "already_decoded"
                                }
                                
                                results["details"].append(block_result)
                                batch_results["blocks"].append(block_result)
                        
                        if not skip_processing:
                            # Process the block
                            success, result_info = self.processor.process_block(path)
                            
                            block_result = {
                                "path": path,
                                "block_number": block_number,
                                "success": success,
                                "info": result_info
                            }
                            
                            if success:
                                results["success"] += 1
                                batch_results["success"] += 1
                            else:
                                results["failure"] += 1
                                batch_results["failure"] += 1
                            
                            results["details"].append(block_result)
                            batch_results["blocks"].append(block_result)
                        
                        # Update progress
                        progress.update(1)
                        
                        # Periodic status updates for long-running batches
                        current_time = time.time()
                        blocks_processed = i + 1
                        
                        if (blocks_processed % status_interval == 0 or 
                            current_time - last_status_time > status_update_interval):
                            
                            completion_percentage = (blocks_processed / total_blocks) * 100
                            elapsed_time = current_time - batch_start_time.timestamp()
                            blocks_per_second = blocks_processed / elapsed_time if elapsed_time > 0 else 0
                            
                            est_remaining_seconds = ((total_blocks - blocks_processed) / 
                                                    blocks_per_second if blocks_per_second > 0 else float('inf'))
                            est_remaining = str(datetime.timedelta(seconds=int(est_remaining_seconds)))
                            
                            self.logger.info(
                                f"Status update: {blocks_processed}/{total_blocks} blocks processed "
                                f"({completion_percentage:.1f}%) - "
                                f"{batch_results['success']} successful, {batch_results['failure']} failed, "
                                f"{batch_results['skipped']} skipped. "
                                f"Rate: {blocks_per_second:.2f} blocks/sec. "
                                f"Est. remaining: {est_remaining}"
                            )
                            
                            last_status_time = current_time
                        
                    except Exception as e:
                        self.logger.error(f"Error processing {path}: {str(e)}")
                        results["failure"] += 1
                        batch_results["failure"] += 1
                        
                        try:
                            block_number = env.extract_block_number(path)
                        except:
                            block_number = None
                        
                        error_result = {
                            "path": path,
                            "block_number": block_number,
                            "success": False,
                            "error": str(e)
                        }
                        
                        results["details"].append(error_result)
                        batch_results["blocks"].append(error_result)
                        progress.update(1)
            
            # Finalize batch results
            batch_end_time = datetime.now()
            batch_results["ended_at"] = batch_end_time.isoformat()
            batch_results["duration_seconds"] = (batch_end_time - batch_start_time).total_seconds()
            
            # Log batch summary
            self.logger.info(
                f"Batch {batch_index + 1} complete: "
                f"{batch_results['success']} successful, "
                f"{batch_results['failure']} failed, "
                f"{batch_results['skipped']} skipped, "
                f"in {batch_results['duration_seconds']:.2f} seconds"
            )
            
            # Add to overall results
            results["batches"].append(batch_results)
            
            # Optional: Add a brief pause between batches
            if batch_index < len(batches) - 1:
                time.sleep(1)  # Prevent potential resource contention
        
        # Finalize overall results
        results["ended_at"] = datetime.now().isoformat()
        results["duration_seconds"] = (
            datetime.fromisoformat(results["ended_at"]) - 
            datetime.fromisoformat(results["started_at"])
        ).total_seconds()
        
        # Log overall summary
        self.logger.info(
            f"Processing complete: "
            f"{results['success']} successful, "
            f"{results['failure']} failed, "
            f"{results['skipped']} skipped, "
            f"in {results['duration_seconds']:.2f} seconds"
        )
        
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
            # Auto-generate filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            if self.storage_type == "local":
                output_dir = Path(self.local_dir or env.get_path('data_dir'))
            else:
                output_dir = env.get_path('data_dir')
            
            output_file = output_dir / f"batch_results_{timestamp}.json"
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        # Save results
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        self.logger.info(f"Results saved to {output_file}")
        return str(output_file)