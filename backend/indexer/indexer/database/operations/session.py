from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import create_engine

from ..models.base import Base

class ConnectionManager:
    def __init__(self, database_url: str):
        self.engine = create_engine(database_url)
        self._initialize_tables()
    
    def _initialize_tables(self):
        Base.metadata.create_all(self.engine)

    @contextmanager
    def get_session(self):
        session = Session(self.engine)
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()