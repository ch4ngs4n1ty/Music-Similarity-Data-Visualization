"""
Database Creation Script
=========================
This script creates all the tables in your database.

What it does:
1. Reads the table definitions from backend/models.py
2. Creates a new SQLite database file (music_similarity.db)
3. Creates all tables: artists, albums, tracks, audio_features, embeddings, neighbors

When to run:
- First time setting up the project
- After deleting the database file
- After changing table structure in models.py

How to run:
    python create_db.py

Note: If tables already exist, this won't overwrite them
"""

from backend.database import engine, Base
# Import all models so SQLAlchemy knows about them
from backend.models import Artist, Album, Track, AudioFeature, Embedding, Neighbor

def create_database():
    """
    Create all database tables.
    
    This uses SQLAlchemy to generate SQL commands like:
        CREATE TABLE artists (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            ...
        );
    
    It automatically creates all tables defined in models.py
    """
    Base.metadata.create_all(bind=engine)
    print("✅ Database created successfully!")
    print("   File location: ./music_similarity.db")
    print("   Tables created: artists, albums, tracks, audio_features, embeddings, neighbors")

if __name__ == "__main__":
    create_database()

