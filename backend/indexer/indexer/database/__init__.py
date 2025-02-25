# database/__init__.py
from .models.base import Base
from .operations.session import engine

def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(bind=engine)