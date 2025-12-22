import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.database import SessionLocal
from backend.models import Artist, Track, AudioFeature

def view_data():
    db = SessionLocal()
    
    print("\n=== ARTISTS ===")
    artists = db.query(Artist).limit(10).all()
    for artist in artists:
        print(f"{artist.id}: {artist.name}")
    
    print("\n=== TRACKS ===")
    tracks = db.query(Track).limit(10).all()
    for track in tracks:
        print(f"{track.id}: {track.name} (Artist ID: {track.artist_id})")
    
    print("\n=== AUDIO FEATURES ===")
    features = db.query(AudioFeature).limit(5).all()
    for f in features:
        print(f"Track {f.track_id}: Energy={f.energy}, Valence={f.valence}, Tempo={f.tempo}")
    
    print("\n=== DATABASE STATS ===")
    print(f"Total Artists: {db.query(Artist).count()}")
    print(f"Total Tracks: {db.query(Track).count()}")
    print(f"Total Audio Features: {db.query(AudioFeature).count()}")
    
    db.close()

if __name__ == "__main__":
    view_data()

