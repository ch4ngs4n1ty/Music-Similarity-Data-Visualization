from backend.database import engine, Base
from backend.models import Artist, Album, Track, AudioFeature, Embedding, Neighbor

def create_database():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
    print("✅ Database created successfully!")

if __name__ == "__main__":
    create_database()

