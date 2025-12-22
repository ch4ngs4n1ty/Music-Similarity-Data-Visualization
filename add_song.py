"""
========================================
MUSIC SIMILARITY - ADD SONG SCRIPT
========================================

This is the MAIN script that brings everything together!

WHAT IT DOES:
1. Searches for a song on Spotify (gets metadata: artist, album, etc.)
2. Downloads the audio from YouTube (gets actual audio file)
3. Extracts audio features using librosa (analyzes the sound)
4. Stores everything in the database
5. Calculates and shows similar songs

HOW TO USE:
    python add_song.py "Song Name"
    
    OR run without arguments:
    python add_song.py
    (it will ask you for the song name)

EXAMPLE:
    python add_song.py "Blinding Lights"
    
    Output:
    - Downloads the song
    - Shows audio features (tempo, energy, etc.)
    - Shows similar songs from your database
    
REQUIREMENTS:
- .env file with Spotify credentials
- Internet connection (for Spotify API and YouTube downloads)
- ffmpeg installed (for audio processing)
"""

# ============================================================================
# IMPORTS - Libraries we need
# ============================================================================
import os  # For file/folder operations
from dotenv import load_dotenv  # To load secrets from .env file
import spotipy  # Spotify API library
from spotipy.oauth2 import SpotifyClientCredentials  # Spotify authentication
import yt_dlp  # YouTube downloader
import librosa  # Audio analysis library
import numpy as np  # Math/array operations
from backend.database import SessionLocal  # Database connection
from backend.models import Artist, Album, Track, AudioFeature  # Database tables
from sklearn.metrics.pairwise import cosine_similarity  # Similarity calculation

# Load environment variables from .env file (Spotify credentials)
load_dotenv()

# ============================================================================
# STEP 1: SEARCH SPOTIFY
# ============================================================================
def search_spotify(song_name):
    """
    Search for a song on Spotify and get its metadata.
    
    Args:
        song_name (str): Name of the song to search for
        
    Returns:
        dict: Song information including:
            - name: Track name
            - artist: Artist name
            - album: Album name
            - spotify_id: Spotify's unique ID for this track
        
        None: If song not found
    
    Example:
        >>> search_spotify("Blinding Lights")
        {
            'name': 'Blinding Lights',
            'artist': 'The Weeknd',
            'album': 'After Hours',
            'spotify_id': '0VjIjW4GlUZAMYd2vXMi3b'
        }
    """
    # Get Spotify credentials from .env file
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    # Authenticate with Spotify
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Search for the song (limit=1 means just get the best match)
    results = sp.search(q=song_name, type='track', limit=1)
    
    # If we found something, extract the info we need
    if results['tracks']['items']:
        track = results['tracks']['items'][0]
        return {
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'album': track['album']['name'],
            'spotify_id': track['id'],
        }
    return None

# ============================================================================
# STEP 2: DOWNLOAD AUDIO FROM YOUTUBE
# ============================================================================
def download_audio(artist, track_name):
    """
    Download audio from YouTube.
    
    How it works:
    1. Searches YouTube for "{artist} {track_name}"
    2. Downloads the first result
    3. Converts to MP3
    4. Saves to audio_cache/ folder
    
    Args:
        artist (str): Artist name
        track_name (str): Track name
        
    Returns:
        str: Path to downloaded MP3 file
        None: If download fails
        
    Example:
        >>> download_audio("The Weeknd", "Blinding Lights")
        "audio_cache/The Weeknd - Blinding Lights.mp3"
    """
    query = f"{artist} {track_name}"  # Combine for YouTube search
    output_dir = 'audio_cache'  # Folder to store downloaded audio
    os.makedirs(output_dir, exist_ok=True)  # Create folder if it doesn't exist
    
    # yt-dlp configuration
    ydl_opts = {
        'format': 'bestaudio/best',  # Get best quality audio
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',  # Use ffmpeg to extract audio
            'preferredcodec': 'mp3',  # Convert to MP3
            'preferredquality': '192',  # 192 kbps quality
        }],
        'outtmpl': os.path.join(output_dir, f'{artist} - {track_name}.%(ext)s'),  # Output filename
        'quiet': True,  # Don't show too much output
        'no_warnings': True,  # Suppress warnings
        'default_search': 'ytsearch1',  # Search YouTube, get first result
    }
    
    try:
        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if 'entries' in info:
                filepath = os.path.join(output_dir, f'{artist} - {track_name}.mp3')
                return filepath
    except Exception as e:
        print(f"❌ Error downloading: {e}")
    return None

# ============================================================================
# STEP 3: EXTRACT AUDIO FEATURES
# ============================================================================
def extract_features(filepath):
    """
    Extract audio features from an MP3 file using librosa.
    
    This is where the REAL magic happens! We analyze the actual audio
    to extract numerical features that describe how the song sounds.
    
    Features extracted:
    - tempo: How fast the song is (BPM = Beats Per Minute)
    - energy: How intense/loud the song is (0-1)
    - danceability: How easy to dance to (0-1) - approximated from rhythm
    - valence: How positive/happy the song sounds (0-1) - approximated
    
    Args:
        filepath (str): Path to the MP3 file
        
    Returns:
        dict: Audio features {tempo, energy, danceability, valence}
        None: If extraction fails
        
    Example:
        >>> extract_features("audio_cache/The Weeknd - Blinding Lights.mp3")
        {
            'tempo': 103.4,
            'energy': 0.145,
            'danceability': 0.037,
            'valence': 0.484
        }
    """
    try:
        # Load audio file (limit to 30 seconds to save time)
        # y = audio signal (array of sound wave values)
        # sr = sample rate (usually 22050 Hz)
        y, sr = librosa.load(filepath, duration=30)
        
        # TEMPO: Detect the beat and calculate BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # ENERGY: Calculate RMS (root mean square) energy
        # Higher values = louder, more energetic song
        rms = librosa.feature.rms(y=y)[0]
        
        # DANCEABILITY (proxy): Zero crossing rate
        # Measures how often the sound wave crosses zero
        # Higher values = more percussive, rhythmic
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # VALENCE (proxy): Chroma features (harmony/pitch)
        # Brighter harmonies tend to sound happier
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # Convert to Python floats (from numpy)
        # Handle both array and scalar tempo values
        return {
            'tempo': float(tempo[0] if hasattr(tempo, '__len__') else tempo),
            'energy': float(np.mean(rms)),
            'danceability': float(np.mean(zcr)),
            'valence': float(np.mean(chroma)),
        }
    except Exception as e:
        print(f"❌ Error extracting features: {e}")
        return None

# ============================================================================
# STEP 4: STORE IN DATABASE
# ============================================================================
def store_in_database(track_info, features):
    """
    Store the track and its features in the database.
    
    This function:
    1. Creates/finds the Artist
    2. Creates/finds the Album
    3. Creates the Track (checks if already exists)
    4. Stores the AudioFeatures
    
    Args:
        track_info (dict): Song metadata from Spotify
        features (dict): Audio features from librosa
        
    Returns:
        int: The track_id of the stored track
        None: If storage fails
    """
    db = SessionLocal()  # Open database connection
    
    try:
        # -------------------- ARTIST --------------------
        # Check if artist already exists
        artist = db.query(Artist).filter_by(name=track_info['artist']).first()
        if not artist:
            # Create new artist
            artist = Artist(name=track_info['artist'], spotify_id=None)
            db.add(artist)
            db.flush()  # Save to get the artist.id
        
        # -------------------- ALBUM --------------------
        # Check if album already exists for this artist
        album = db.query(Album).filter_by(
            name=track_info['album'],
            artist_id=artist.id
        ).first()
        if not album:
            # Create new album
            album = Album(
                name=track_info['album'],
                artist_id=artist.id,
                spotify_id=None
            )
            db.add(album)
            db.flush()  # Save to get the album.id
        
        # -------------------- TRACK --------------------
        # Check if this exact track already exists
        track = db.query(Track).filter_by(spotify_id=track_info['spotify_id']).first()
        if track:
            print(f"⚠️  Track already exists in database")
            return track.id
        
        # Create new track
        track = Track(
            name=track_info['name'],
            artist_id=artist.id,
            album_id=album.id,
            spotify_id=track_info['spotify_id'],
            preview_url=None
        )
        db.add(track)
        db.flush()  # Save to get the track.id
        
        # -------------------- AUDIO FEATURES --------------------
        # Store the extracted audio features
        audio_feature = AudioFeature(
            track_id=track.id,
            energy=features['energy'],
            valence=features['valence'],
            tempo=features['tempo'],
            danceability=features['danceability']
        )
        db.add(audio_feature)
        
        # Commit all changes to database
        db.commit()
        print(f"✅ Stored in database (Track ID: {track.id})")
        return track.id
        
    except Exception as e:
        db.rollback()  # Undo changes if there was an error
        print(f"❌ Database error: {e}")
        return None
    finally:
        db.close()  # Always close the database connection

# ============================================================================
# STEP 5: FIND SIMILAR SONGS
# ============================================================================
def find_similar_songs(track_id, limit=5):
    """
    Find songs similar to the given track based on audio features.
    
    How it works:
    1. Get the audio features for the current track
    2. Get features for all other tracks in database
    3. Calculate cosine similarity (how "close" the features are)
    4. Sort by similarity score
    5. Return top N similar songs
    
    Cosine Similarity Explained:
    - Compares feature vectors as if they're points in space
    - 1.0 = identical features
    - 0.0 = completely different
    - 0.9+ = very similar
    
    Args:
        track_id (int): ID of the track to find similarities for
        limit (int): How many similar songs to return (default: 5)
        
    Returns:
        list: List of similar songs with their info and similarity scores
        
    Example return:
        [
            {
                'track': 'Starboy',
                'artist': 'The Weeknd',
                'similarity': 0.989,
                'features': {...}
            },
            ...
        ]
    """
    db = SessionLocal()
    
    try:
        # Get features for the current track
        current = db.query(AudioFeature).filter_by(track_id=track_id).first()
        if not current:
            print("❌ No features found for this track")
            return []
        
        # Get features for all OTHER tracks (not the current one)
        all_features = db.query(AudioFeature).filter(
            AudioFeature.track_id != track_id
        ).all()
        
        if not all_features:
            print("ℹ️  No other tracks in database yet")
            return []
        
        # Create feature vector for current track
        # We normalize tempo by dividing by 200 to keep all values 0-1
        current_vector = np.array([[
            current.energy,
            current.valence,
            current.tempo / 200,  # Normalize tempo to 0-1 range
            current.danceability
        ]])
        
        # Calculate similarity for each track
        similarities = []
        for feature in all_features:
            # Create feature vector for this track
            other_vector = np.array([[
                feature.energy,
                feature.valence,
                feature.tempo / 200,
                feature.danceability
            ]])
            
            # Calculate cosine similarity (0 to 1)
            # Higher = more similar
            similarity = cosine_similarity(current_vector, other_vector)[0][0]
            
            # Get track and artist info
            track = db.query(Track).filter_by(id=feature.track_id).first()
            artist = db.query(Artist).filter_by(id=track.artist_id).first()
            
            # Add to results list
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
        
        # Sort by similarity (highest first)
        similarities.sort(key=lambda x: x['similarity'], reverse=True)
        
        # Return top N results
        return similarities[:limit]
        
    finally:
        db.close()

# ============================================================================
# MAIN FUNCTION: Bring it all together!
# ============================================================================
def add_song(song_name):
    """
    Complete pipeline to add a song and find similar tracks.
    
    This is the main function that orchestrates everything:
    1. Search Spotify
    2. Download from YouTube
    3. Extract features
    4. Store in database
    5. Find similar songs
    
    Args:
        song_name (str): Name of the song to add
    """
    print("\n" + "="*60)
    print(f"🎵 Adding Song: {song_name}")
    print("="*60 + "\n")
    
    # ========== STEP 1: Search Spotify ==========
    print("1️⃣  Searching Spotify...")
    track_info = search_spotify(song_name)
    if not track_info:
        print("❌ Song not found on Spotify")
        return
    
    print(f"✅ Found: {track_info['name']} by {track_info['artist']}")
    
    # ========== STEP 2: Download from YouTube ==========
    print("\n2️⃣  Downloading audio from YouTube...")
    filepath = download_audio(track_info['artist'], track_info['name'])
    if not filepath:
        print("❌ Failed to download audio")
        return
    print(f"✅ Downloaded to: {filepath}")
    
    # ========== STEP 3: Extract features ==========
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
    
    # ========== STEP 4: Store in database ==========
    print("\n4️⃣  Storing in database...")
    track_id = store_in_database(track_info, features)
    if not track_id:
        return
    
    # ========== STEP 5: Find similar songs ==========
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

# ============================================================================
# RUN THE SCRIPT
# ============================================================================
if __name__ == "__main__":
    import sys
    
    # Check if song name was provided as command-line argument
    if len(sys.argv) > 1:
        # Join all arguments (in case song name has spaces)
        song_name = " ".join(sys.argv[1:])
    else:
        # Ask user for song name
        song_name = input("🎵 Enter song name: ")
    
    # Run the main function
    add_song(song_name)
