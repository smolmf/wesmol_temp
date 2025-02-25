from typing import List, Optional
from datetime import datetime
from sqlalchemy import desc

from indexer.indexer.database.models.status import ProcessingStatus, BlockProcess
from indexer.indexer.database.operations.session import ConnectionManager


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