from typing import Tuple, Optional, Dict, Any, List


from indexer.indexer.storage.base import GCSBaseHandler
from indexer.indexer.database.models.status import ProcessingStatus
from indexer.indexer.database.operations.manager import DatabaseManager
from indexer.indexer.processing.validator import BlockValidator
from indexer.indexer.storage.handler import BlockHandler 
from indexer.indexer.decoders.block import BlockDecoder


class BlockProcessor:
    """
    Handles block processing from GCS RPC block files to GCS decoded block files. Maintains processing status.
    """
    
    def __init__(self, 
                 gcs_handler: GCSBaseHandler, 
                 status_tracker: DatabaseManager,
                 validator: Optional[BlockValidator] = None,
                 decoder: Optional[BlockDecoder] = None, # TODO: Needs a default registry?
                 handler: Optional[BlockHandler] = None):

        self.gcs_handler = gcs_handler
        self.status_tracker = status_tracker
        # Create defaults for components if not provided
        self.validator = validator or BlockValidator()
        self.decoder = decoder or BlockDecoder()
        self.handler = handler or BlockHandler(gcs_handler)
    
    def process_block(self, gcs_path: str) -> Tuple[bool, Dict[str, Any]]:
        """
        Process a block from GCS through validation, decoding, and storage.
        
        Returns:
            Tuple of (success, result_info)
        """
        result_info = {
            "validation": False,
            "decoding": False,
            "storage": False,
            "errors": []
        }
        
        try:
            block_number = self.handler.extract_block_number(gcs_path)
            
            self.status_tracker.record_block(
                block_number=block_number,
                gcs_path=gcs_path,
                status=ProcessingStatus.PROCESSING
            )
            
            block_data = self.gcs_handler.download_blob_as_bytes(gcs_path)
            if not block_data:
                error_msg = f"Failed to download block from {gcs_path}"
                result_info["errors"].append(error_msg)
                self.status_tracker.update_status(
                    block_number=block_number,
                    status=ProcessingStatus.INVALID,
                    error_message=error_msg
                )
                return False, result_info
            
            is_valid, error, raw_block = self.validator.validate_block_data(block_data)
            
            if not is_valid:
                self.status_tracker.update_status(
                    block_number=block_number,
                    status=ProcessingStatus.INVALID,
                    error_message=error
                )
                result_info["errors"].append(f"Validation failed: {error}")
                return False, result_info
            
            result_info["validation"] = True
            
            try:
                decoded_data = self.decoder.decode_block(raw_block)
                result_info["decoding"] = True
            except Exception as e:
                error_msg = f"Decoding failed: {str(e)}"
                result_info["errors"].append(error_msg)
                self.status_tracker.update_status(
                    block_number=block_number,
                    status=ProcessingStatus.INVALID,
                    error_message=error_msg
                )
                return False, result_info
            
            try:
                self.handler.store_decoded_block(block_number, decoded_data)
                result_info["storage"] = True
            except Exception as e:
                error_msg = f"Storage failed: {str(e)}"
                result_info["errors"].append(error_msg)
                self.status_tracker.update_status(
                    block_number=block_number,
                    status=ProcessingStatus.INVALID,
                    error_message=error_msg
                )
                return False, result_info
            
            self.status_tracker.update_status(
                block_number=block_number,
                status=ProcessingStatus.VALID
            )
            
            return True, result_info
            
        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            result_info["errors"].append(error_msg)
            
            if 'block_number' in locals():
                self.status_tracker.update_status(
                    block_number=block_number,
                    status=ProcessingStatus.INVALID,
                    error_message=error_msg
                )
            return False, result_info
    
    def reprocess_block(self, block_number: int) -> Tuple[bool, Dict[str, Any]]:
        """
        Reprocess a block by block number.
        
        Returns:
            Tuple of (success, result_info)
        """
        block_record = self.status_tracker.get_block(block_number)
        if not block_record:
            return False, {"errors": [f"Block {block_number} not found in records"]}
        
        return self.process_block(block_record.gcs_path)
    
    def reprocess_blocks(self, block_numbers: List[int]) -> Dict[str, Any]:
        """
        Reprocess multiple blocks by block number.
        
        Returns:
            Dictionary with processing results
        """
        results = {
            "total": len(block_numbers),
            "success": 0,
            "failure": 0,
            "details": []
        }
        
        for block_number in block_numbers:
            success, result_info = self.reprocess_block(block_number)
            
            if success:
                results["success"] += 1
            else:
                results["failure"] += 1
                
            results["details"].append({
                "block_number": block_number,
                "success": success,
                "info": result_info
            })
        
        return results