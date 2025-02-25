"""
Database initialization script for WESMOL Indexer.
"""

import sys
from pathlib import Path
import argparse

# Add parent directory to path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent.parent
sys.path.append(str(backend_dir))

from indexer.indexer.env import env
from indexer.indexer.database.models.base import Base
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

def init_db(drop_tables=False):
    """Initialize the database tables."""
    database_url = env.get_db_url()
    print(f"Connecting to database at {database_url}")
    
    engine = create_engine(database_url)
    
    try:
        if drop_tables:
            print("Dropping all tables...")
            Base.metadata.drop_all(engine)
            print("Tables dropped successfully.")
        
        print("Creating tables...")
        Base.metadata.create_all(engine)
        print("Tables created successfully.")
        
        return True
    except SQLAlchemyError as e:
        print(f"Error initializing database: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Initialize WESMOL Indexer database")
    parser.add_argument("--drop", action="store_true", help="Drop existing tables before creating")
    args = parser.parse_args()
    
    success = init_db(args.drop)
    
    if success:
        print("Database initialization completed successfully")
        sys.exit(0)
    else:
        print("Database initialization failed")
        sys.exit(1)

if __name__ == "__main__":
    main()