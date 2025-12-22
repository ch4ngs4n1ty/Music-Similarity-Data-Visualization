"""
Complete pipeline: Add a song and find similar tracks
1. Search song on Spotify
2. Download audio from YouTube
3. Extract features with librosa
4. Store in database
5. Calculate and show similar songs
"""

import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import yt_dlp
import librosa
import numpy as np
from backend.database import SessionLocal
from backend.models import Artist, Album, Track, AudioFeature
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

def search_spotify(song_name):
    """Search for song on Spotify."""
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    results = sp.search(q=song_name, type='track', limit=1)
    
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        return {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'spotify_id': track['id'],
        }
    return None

def download_audio(artist, track_name):
    """Download audio from YouTube."""
    query = f"{artist} {track_name}"
    output_dir = 'audio_cache'
    os.makedirs(output_dir, exist_ok=True)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, f'{artist} - {track_name}.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if 'entries' in info:
                filepath = os.path.join(output_dir, f'{artist} - {track_name}.mp3')
                return filepath
    except Exception as e:
        print(f"❌ Error downloading: {e}")
    return None

def extract_features(filepath):
    """Extract audio features using librosa."""
    try:
        y, sr = librosa.load(filepath, duration=30)
        
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)[0]
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        return {
            'tempo': float(tempo[0] if hasattr(tempo, '__len__') else tempo),
            'energy': float(np.mean(rms)),
            'danceability': float(np.mean(zcr)),
            'valence': float(np.mean(chroma)),
        }
    except Exception as e:
        print(f"❌ Error extracting features: {e}")
        return None

def store_in_database(track_info, features):
    """Store track and features in database."""
    db = SessionLocal()
    
    try:
        # Get or create artist
        artist = db.query(Artist).filter_by(name=track_info['artist']).first()
        if not artist:
            artist = Artist(name=track_info['artist'], spotify_id=None)
            db.add(artist)
            db.flush()
        
        # Get or create album
        album = db.query(Album).filter_by(name=track_info['album'], artist_id=artist.id).first()
        if not album:
            album = Album(name=track_info['album'], artist_id=artist.id, spotify_id=None)
            db.add(album)
            db.flush()
        
        # Check if track exists
        track = db.query(Track).filter_by(spotify_id=track_info['spotify_id']).first()
        if track:
            print(f"⚠️  Track already exists in database")
            return track.id
        
        # Create track
        track = Track(
            name=track_info['name'],
            artist_id=artist.id,
            album_id=album.id,
            spotify_id=track_info['spotify_id'],
            preview_url=None
        )
        db.add(track)
        db.flush()
        
        # Add audio features
        audio_feature = AudioFeature(
            track_id=track.id,
            energy=features['energy'],
            valence=features['valence'],
            tempo=features['tempo'],
            danceability=features['danceability']
        )
        db.add(audio_feature)
        
        db.commit()
        print(f"✅ Stored in database (Track ID: {track.id})")
        return track.id
        
    except Exception as e:
        db.rollback()
        print(f"❌ Database error: {e}")
        return None
    finally:
        db.close()

def find_similar_songs(track_id, limit=5):
    """Find similar songs based on audio features."""
    db = SessionLocal()
    
    try:
        # Get current track features
        current = db.query(AudioFeature).filter_by(track_id=track_id).first()
        if not current:
            print("❌ No features found for this track")
            return []
        
        # Get all other tracks with features
        all_features = db.query(AudioFeature).filter(AudioFeature.track_id != track_id).all()
        
        if not all_features:
            print("ℹ️  No other tracks in database yet")
            return []
        
        # Calculate similarity
        current_vector = np.array([[current.energy, current.valence, current.tempo/200, current.danceability]])
        
        similarities = []
        for feature in all_features:
            other_vector = np.array([[feature.energy, feature.valence, feature.tempo/200, feature.danceability]])
            similarity = cosine_similarity(current_vector, other_vector)[0][0]
            
            track = db.query(Track).filter_by(id=feature.track_id).first()
            artist = db.query(Artist).filter_by(id=track.artist_id).first()
            
            similarities.append({
                'track': track.name,
                'artist': artist.name,
                'similarity': similarity,
                'features': {
                    'energy': feature.energy,
                    'valence': feature.valence,
                    'tempo': feature.tempo,
                    'danceability': feature.danceability
                }
            })
        
        # Sort by similarity
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return similarities[:limit]
        
    finally:
        db.close()

def add_song(song_name):
    """Complete pipeline to add a song and find similar tracks."""
    print("\n" + "="*60)
    print(f"🎵 Adding Song: {song_name}")
    print("="*60 + "\n")
    
    # Step 1: Search Spotify
    print("1️⃣  Searching Spotify...")
    track_info = search_spotify(song_name)
    if not track_info:
        print("❌ Song not found on Spotify")
        return
    
    print(f"✅ Found: {track_info['name']} by {track_info['artist']}")
    
    # Step 2: Download from YouTube
    print("\n2️⃣  Downloading audio from YouTube...")
    filepath = download_audio(track_info['artist'], track_info['name'])
    if not filepath:
        print("❌ Failed to download audio")
        return
    print(f"✅ Downloaded to: {filepath}")
    
    # Step 3: Extract features
    print("\n3️⃣  Extracting audio features...")
    features = extract_features(filepath)
    if not features:
        print("❌ Failed to extract features")
        return
    print(f"✅ Features extracted:")
    print(f"   Tempo: {features['tempo']:.1f} BPM")
    print(f"   Energy: {features['energy']:.3f}")
    print(f"   Danceability: {features['danceability']:.3f}")
    print(f"   Valence: {features['valence']:.3f}")
    
    # Step 4: Store in database
    print("\n4️⃣  Storing in database...")
    track_id = store_in_database(track_info, features)
    if not track_id:
        return
    
    # Step 5: Find similar songs
    print("\n5️⃣  Finding similar songs...")
    similar = find_similar_songs(track_id)
    
    if similar:
        print(f"\n🎯 Top {len(similar)} Similar Songs:")
        print("-"*60)
        for i, song in enumerate(similar, 1):
            print(f"\n{i}. {song['track']} by {song['artist']}")
            print(f"   Similarity: {song['similarity']:.1%}")
            print(f"   Why similar:")
            print(f"     Energy: {song['features']['energy']:.3f} (yours: {features['energy']:.3f})")
            print(f"     Tempo: {song['features']['tempo']:.1f} BPM (yours: {features['tempo']:.1f})")
    else:
        print("\nℹ️  Add more songs to see similarities!")
    
    print("\n" + "="*60)
    print("✨ Done!")
    print("="*60 + "\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        song_name = " ".join(sys.argv[1:])
    else:
        song_name = input("🎵 Enter song name: ")
    
    add_song(song_name)

