from typing import List, Optional
from datetime import datetime
from sqlalchemy import desc

from ..models.status import ProcessingStatus, BlockProcess
from ..models.gcs import GcsObject
from .session import ConnectionManager
from ...processing.factory import ComponentFactory


class DatabaseManager:
    def __init__(self, db_conn: ConnectionManager):
        self.db = db_conn

    def record_block(self, block_number: int, gcs_path: str, 
                    status: ProcessingStatus = ProcessingStatus.PENDING) -> BlockProcess:
        """Record or update a block's validation status."""
        with self.db.get_session() as session:
            block = session.query(BlockProcess).get(block_number)
            if block:
                block.status = status
                block.gcs_path = gcs_path
                block.updated_at = datetime.now()
            else:
                block = BlockProcess(
                    block_number=block_number,
                    gcs_path=gcs_path,
                    status=status
                )
                session.add(block)
            session.commit()
            return block

    def update_status(self, block_number: int, status: ProcessingStatus, 
                     error_message: Optional[str] = None) -> BlockProcess:
        """Update validation status for a block."""
        with self.db.get_session() as session:
            block = session.query(BlockProcess).get(block_number)
            if not block:
                raise ValueError(f"Block {block_number} not found")
            
            block.status = status
            block.error_message = error_message
            block.updated_at = datetime.now()
            session.commit()
            return block

    def get_blocks_by_status(self, status: ProcessingStatus, 
                           limit: int = 100) -> List[BlockProcess]:
        """Get blocks with a specific status."""
        with self.db.get_session() as session:
            return session.query(BlockProcess)\
                .filter(BlockProcess.status == status)\
                .order_by(desc(BlockProcess.block_number))\
                .limit(limit)\
                .all()

    def get_block(self, block_number: int) -> Optional[BlockProcess]:
        """Get a specific block's validation status."""
        with self.db.get_session() as session:
            return session.query(BlockProcess).get(block_number)
        
    def sync_gcs_objects(self, prefix=None, limit=None):
        """
        Sync GCS objects to database.
        
        Args:
            prefix: Optional prefix to filter GCS objects
            limit: Optional limit to number of objects to sync
            
        Returns:
            Count of objects synced
        """
        
        gcs_handler = ComponentFactory.get_gcs_handler()
        
        # List objects from GCS
        blobs = gcs_handler.list_blobs(prefix=prefix)
        if limit:
            blobs = list(itertools.islice(blobs, limit))
        
        count = 0
        with self.db.get_session() as session:
            for blob in blobs:
                # Try to extract block number from path
                block_number = None
                try:
                    # Assuming format like "raw/block_12345.json"
                    filename = blob.name.split('/')[-1]
                    if filename.startswith('block_') and filename.endswith('.json'):
                        block_number = int(filename[6:-5])  # Extract "12345" from "block_12345.json"
                except:
                    pass
                
                # Determine file type
                file_type = 'unknown'
                if 'raw/' in blob.name:
                    file_type = 'raw'
                elif 'decoded/' in blob.name:
                    file_type = 'decoded'
                
                # Create or update record
                obj = session.query(GcsObject).filter(GcsObject.path == blob.name).first()
                if obj:
                    obj.block_number = block_number
                    obj.file_type = file_type
                    obj.size = blob.size
                    obj.updated_at = datetime.now()
                else:
                    obj = GcsObject(
                        path=blob.name,
                        block_number=block_number,
                        file_type=file_type,
                        size=blob.size
                    )
                    session.add(obj)
                
                count += 1
                
                # Commit in batches to avoid memory issues
                if count % 100 == 0:
                    session.commit()
            
            session.commit()
        
        return count

    def get_available_block_paths(self, file_type='raw', min_block=None, max_block=None, limit=None):
        """
        Get available block paths from database.
        
        Args:
            file_type: Type of files to get ('raw' or 'decoded')
            min_block: Optional minimum block number
            max_block: Optional maximum block number
            limit: Optional limit to number of results
            
        Returns:
            List of block paths
        """
        
        with self.db.get_session() as session:
            query = session.query(GcsObject.path).filter(GcsObject.file_type == file_type)
            
            if min_block is not None:
                query = query.filter(GcsObject.block_number >= min_block)
            
            if max_block is not None:
                query = query.filter(GcsObject.block_number <= max_block)
            
            if limit:
                query = query.limit(limit)
            
            return [row[0] for row in query.all()]

    def block_exists_in_gcs(self, block_number, file_type='raw'):
        """
        Check if a block exists in GCS.
        
        Args:
            block_number: Block number to check
            file_type: Type of file to check for ('raw' or 'decoded')
            
        Returns:
            True if block exists, False otherwise
        """
        
        with self.db.get_session() as session:
            return session.query(GcsObject).filter(
                GcsObject.block_number == block_number,
                GcsObject.file_type == file_type
            ).count() > 0