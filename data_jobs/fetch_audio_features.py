import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from backend.database import SessionLocal
from backend.models import Track, AudioFeature

load_dotenv()

def fetch_audio_features():
    """Fetch audio features for tracks that don't have them."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    db = SessionLocal()
    
    try:
        # Get tracks without audio features
        tracks = db.query(Track).outerjoin(AudioFeature).filter(AudioFeature.id == None).all()
        
        print(f"Found {len(tracks)} tracks without audio features")
        
        for track in tracks:
            try:
                features = sp.audio_features([track.spotify_id])[0]
                if features:
                    audio_feature = AudioFeature(
                        track_id=track.id,
                        energy=features.get('energy'),
                        valence=features.get('valence'),
                        tempo=features.get('tempo'),
                        danceability=features.get('danceability')
                    )
                    db.add(audio_feature)
                    print(f"✓ Fetched features for: {track.name}")
            except Exception as e:
                print(f"✗ Error for {track.name}: {e}")
        
        db.commit()
        print(f"\n✓ Done! Audio features added.")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fetch_audio_features()

