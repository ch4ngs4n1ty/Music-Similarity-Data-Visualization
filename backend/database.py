"""
Database Configuration
======================
This file sets up the connection to our SQLite database.

SQLite is a simple file-based database - no server needed!
The database file is stored as 'music_similarity.db' in your project folder.

Key Components:
- DATABASE_URL: Location of our database file
- engine: The connection to the database
- SessionLocal: Factory for creating database sessions (like opening/closing the database)
- Base: Foundation for all our database models (tables)
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Where our database file is stored
# "sqlite:///./" means: use SQLite, store in current directory
DATABASE_URL = "sqlite:///./music_similarity.db"

# Create the database engine (connection manager)
# check_same_thread=False allows multiple parts of app to use database simultaneously
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal is a class that creates database sessions
# Each session is like "opening" the database to read/write data
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base is the foundation class for all our database tables
# All models (Artist, Track, etc.) will inherit from this
Base = declarative_base()

def get_db():
    """
    Helper function to get a database session.
    
    This is useful for FastAPI endpoints - it automatically:
    1. Opens a database connection
    2. Lets you use it
    3. Closes it when done (even if there's an error)
    
    Example usage:
        db = next(get_db())
        # ... do database operations ...
        db.close()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

