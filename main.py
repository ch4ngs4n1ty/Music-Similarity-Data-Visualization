"""
Spotify Data Fetcher - Get track data by name and artist
"""
from dotenv import load_dotenv
import os
import requests
import json
from typing import Dict, Any, Optional
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import warnings
import urllib3
import logging
import yt_dlp

# Suppress HTTP warnings and errors
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
warnings.filterwarnings('ignore')
logging.getLogger('spotipy').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

load_dotenv()

def get_spotify_client():
    """Get authenticated Spotify client using spotipy"""
    client_id = os.getenv('SPOTIFY_CLIENT_ID') or os.getenv('CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET (or CLIENT_ID and CLIENT_SECRET) must be set in .env file")
    
    auth_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
    return spotipy.Spotify(auth_manager=auth_manager)

def search_track(sp: spotipy.Spotify, track_name: str, artist_name: str = None, show_results: bool = False) -> Optional[Dict[Any, Any]]:
    """
    Search for a track on Spotify by name and optionally artist.
    Uses spotipy library for more reliable searching.
    """
    # Build search query
    if artist_name:
        query = f"{track_name} {artist_name}"
    else:
        query = track_name
    
    try:
        # Search using spotipy (simpler and more reliable)
        results = sp.search(q=query, type='track', limit=10)
        
        tracks = results.get('tracks', {}).get('items', [])
        if not tracks:
            return None
        
        # If artist name provided, try to find best match
        if artist_name:
            artist_lower = artist_name.lower()
            track_lower = track_name.lower()
            
            # First, try exact matches
            for track in tracks:
                track_artists = [a['name'].lower() for a in track.get('artists', [])]
                track_title = track.get('name', '').lower()
                
                # Check if artist matches (fuzzy)
                artist_match = any(artist_lower in artist or artist in artist_lower for artist in track_artists)
                # Check if track name matches (fuzzy)
                track_match = track_lower in track_title or track_title in track_lower
                
                if artist_match and track_match:
                    return track
        
        # Show results if requested
        if show_results:
            print(f"\nFound {len(tracks)} results. Showing top matches:")
            for i, track in enumerate(tracks[:5], 1):
                artists = ', '.join([a['name'] for a in track.get('artists', [])])
                print(f"  {i}. {track.get('name')} by {artists}")
        
        # Return first result (best match from Spotify)
        return tracks[0]
        
    except Exception:
        return None

def get_track_features(sp: spotipy.Spotify, track_id: str) -> Dict[Any, Any]:
    """Get audio features for a track using spotipy"""
    try:
        result = sp.audio_features([track_id])
        return result[0] if result and result[0] else {}
    except Exception:
        return {}

def get_track_analysis(sp: spotipy.Spotify, track_id: str) -> Dict[Any, Any]:
    """Get detailed audio analysis for a track using spotipy"""
    try:
        return sp.audio_analysis(track_id)
    except Exception:
        return {}

def get_track_data(sp: spotipy.Spotify, track_id: str) -> Dict[Any, Any]:
    """Get full track object with all details using spotipy"""
    try:
        return sp.track(track_id)
    except Exception:
        return {}

def extract_unique_attributes(track_data: Dict, features: Dict, analysis: Dict) -> Dict[str, Any]:
    """
    Extract unique attributes representing one data point.
    
    BEST FEATURES FOR MUSIC SIMILARITY (in order of importance):
    1. tempo - Rhythm/BPM (normalize: tempo/200)
    2. energy - Intensity (0-1, already normalized)
    3. danceability - Rhythmic quality (0-1, already normalized)
    4. valence - Positiveness/happiness (0-1, already normalized)
    5. acousticness - Acoustic vs electronic (0-1, already normalized)
    6. loudness - Production loudness (normalize: (loudness+60)/60)
    7. key - Musical key (0-11, normalize: key/11)
    8. mode - Major/minor (0 or 1)
    9. speechiness - Spoken content (0-1, already normalized)
    10. instrumentalness - Instrumental vs vocal (0-1, already normalized)
    
    See SIMILARITY_FEATURES.md for detailed explanation.
    """
    return {
        # Basic identifiers
        'track_id': track_data.get('id'),
        'track_name': track_data.get('name'),
        'artist_name': ', '.join([artist['name'] for artist in track_data.get('artists', [])]),
        'album_name': track_data.get('album', {}).get('name'),
        'release_date': track_data.get('album', {}).get('release_date'),
        
        # Audio features (musical attributes)
        'danceability': features.get('danceability'),
        'energy': features.get('energy'),
        'key': features.get('key'),
        'loudness': features.get('loudness'),
        'mode': features.get('mode'),
        'speechiness': features.get('speechiness'),
        'acousticness': features.get('acousticness'),
        'instrumentalness': features.get('instrumentalness'),
        'liveness': features.get('liveness'),
        'valence': features.get('valence'),
        'tempo': features.get('tempo'),
        'time_signature': features.get('time_signature'),
        'duration_ms': features.get('duration_ms'),
        
        # Track metadata
        'popularity': track_data.get('popularity'),
        'explicit': track_data.get('explicit'),
        'track_number': track_data.get('track_number'),
        'disc_number': track_data.get('disc_number'),
        
        # Analysis summary
        'tempo_confidence': analysis.get('track', {}).get('tempo_confidence', 0),
        'time_signature_confidence': analysis.get('track', {}).get('time_signature_confidence', 0),
        'key_confidence': analysis.get('track', {}).get('key_confidence', 0),
        'mode_confidence': analysis.get('track', {}).get('mode_confidence', 0),
    }

def normalize_track_id(track_id: str) -> str:
    """Normalize track ID from various formats (URI, URL, or plain ID)"""
    # Remove spotify:track: prefix if present
    if track_id.startswith('spotify:track:'):
        return track_id.replace('spotify:track:', '')
    
    # Extract ID from URL if present
    if 'open.spotify.com/track/' in track_id:
        return track_id.split('open.spotify.com/track/')[-1].split('?')[0]
    
    # Remove any query parameters or fragments
    track_id = track_id.split('?')[0].split('#')[0]
    
    return track_id.strip()

def fetch_spotify_data_by_id(track_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetch all Spotify data for a track by its ID
    
    Args:
        track_id: Spotify track ID (can be URI, URL, or plain ID)
    
    Returns:
        Dictionary with all unique attributes, or None if track not found
    """
    # Normalize the track ID
    normalized_id = normalize_track_id(track_id)
    
    try:
        # Get Spotify client
        sp = get_spotify_client()
        
        # Get all data directly by ID
        track_data = get_track_data(sp, normalized_id)
        if not track_data:
            return None
            
        features = get_track_features(sp, normalized_id)
        analysis = get_track_analysis(sp, normalized_id)
        
        # Extract unique attributes
        attributes = extract_unique_attributes(track_data, features, analysis)
        
        return attributes
    except Exception:
        return None

def fetch_spotify_data(track_name: str, artist_name: str = None) -> Optional[Dict[str, Any]]:
    """
    Main function to fetch all Spotify data for a track by name and optionally artist
    
    Args:
        track_name: Name of the track
        artist_name: Name of the artist (optional)
    
    Returns:
        Dictionary with all unique attributes, or None if track not found
    """
    try:
        # Get Spotify client
        sp = get_spotify_client()
        
        # Search for track
        track = search_track(sp, track_name, artist_name)
        if not track:
            return None
        
        track_id = track['id']
        
        # Get all data
        track_data = get_track_data(sp, track_id)
        features = get_track_features(sp, track_id)
        analysis = get_track_analysis(sp, track_id)
        
        # Extract unique attributes
        attributes = extract_unique_attributes(track_data, features, analysis)
        
        return attributes
    except Exception:
        return None

def fetch_with_audio(track_name: str, artist_name: str = None, download: bool = True) -> Optional[Dict[str, Any]]:
    """
    Fetch Spotify data and optionally download audio from YouTube.
    
    Args:
        track_name: Name of the track
        artist_name: Name of the artist (optional)
        download: Whether to download audio (default: True)
    
    Returns:
        Dictionary with attributes and 'audio_path' key if downloaded, or None if track not found
    """
    attributes = fetch_spotify_data(track_name, artist_name)
    if not attributes:
        return None
    
    if download:
        artist = attributes.get('artist_name', '').split(',')[0].strip()
        track = attributes.get('track_name', '')
        if artist and track:
            audio_path = download_audio(artist, track)
            if audio_path:
                attributes['audio_path'] = audio_path
    
    return attributes

def download_audio(artist: str, track_name: str) -> Optional[str]:
    """
    Download audio from YouTube.
    
    Searches YouTube for "{artist} {track_name}" and downloads the first result.
    Converts to MP3 and saves to audio_cache/ folder.
    
    Args:
        artist: Artist name
        track_name: Track name
        
    Returns:
        str: Path to downloaded MP3 file, or None if download fails
    """
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
        error_msg = str(e)
        if 'ffmpeg' in error_msg.lower() or 'ffprobe' in error_msg.lower():
            print(f"\n❌ FFmpeg not found. Please install FFmpeg:")
            print("   Windows: winget install ffmpeg")
            print("   Or download from: https://ffmpeg.org/download.html")
            print("   Make sure ffmpeg is in your PATH and restart terminal/IDE")
        else:
            print(f"❌ Error downloading: {e}")
    return None

def print_attributes(attributes: Dict[str, Any]):
    """Pretty print the attributes"""
    print("\n" + "="*60)
    print("SPOTIFY TRACK DATA - Unique Attributes")
    print("="*60)
    print(json.dumps(attributes, indent=2, ensure_ascii=False))

def test_connection():
    """Test if Spotify API connection works using spotipy"""
    print("Testing Spotify API connection...")
    
    try:
        sp = get_spotify_client()
        print("✓ Successfully authenticated with Spotify")
        
        # Test a simple search
        results = sp.search(q='test', type='track', limit=1)
        
        if results and results.get('tracks', {}).get('items'):
            print("✓ API connection successful!")
            return True
        else:
            print("✗ Search test returned no results")
            return False
            
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        return False
    except Exception as e:
        print(f"✗ Connection test failed: {e}")
        print("\nPossible solutions:")
        print("1. Go to https://developer.spotify.com/dashboard")
        print("2. Select your app")
        print("3. Check if app is in 'Development Mode'")
        print("4. If yes, either:")
        print("   - Add your IP address to 'Users and Access'")
        print("   - Or request to move app out of Development Mode")
        return False

if __name__ == "__main__":
    # Example usage
    print("Spotify Data Fetcher")
    print("="*60)
    
    # Test connection first
    if not test_connection():
        print("\nPlease fix the connection issue before proceeding.")
        exit(1)
    
    print("\n" + "="*60)
    print("Enter either:")
    print("  1. Track ID (e.g., 4uLU6hMCjMI75M1A2tKUQC)")
    print("  2. Track name and artist name")
    print("="*60)
    
    user_input = input("\nEnter track ID (or press Enter to search by name): ").strip()
    
    try:
        if user_input:
            # User provided track ID
            print(f"\nFetching data for track ID: {user_input}...")
            attributes = fetch_spotify_data_by_id(user_input)
            
            if attributes:
                print_attributes(attributes)
                
                # Optionally download audio
                download_choice = input("\nDownload audio from YouTube? (y/n): ").strip().lower()
                if download_choice == 'y':
                    artist = attributes.get('artist_name', '').split(',')[0].strip()
                    track = attributes.get('track_name', '')
                    if artist and track:
                        print(f"\nDownloading audio for '{track}' by {artist}...")
                        audio_path = download_audio(artist, track)
                        if audio_path:
                            print(f"✓ Audio downloaded to: {audio_path}")
                        else:
                            print("✗ Failed to download audio")
            else:
                print(f"Track ID '{user_input}' not found on Spotify")
        else:
            # User wants to search by name
            track_name = input("Enter track name: ").strip()
            artist_name = input("Enter artist name: ").strip()
            
            if not track_name:
                print("Error: Track name is required")
            else:
                print(f"\nSearching for '{track_name}'" + (f" by {artist_name}" if artist_name else "") + "...")
                
                # Fetch data using spotipy
                attributes = fetch_spotify_data(track_name, artist_name)
                
                if attributes:
                    print(f"\n✓ Found: '{attributes.get('track_name')}' by {attributes.get('artist_name')}")
                    print_attributes(attributes)
                    
                    # Optionally download audio
                    download_choice = input("\nDownload audio from YouTube? (y/n): ").strip().lower()
                    if download_choice == 'y':
                        artist = attributes.get('artist_name', '').split(',')[0].strip()
                        track = attributes.get('track_name', '')
                        if artist and track:
                            print(f"\nDownloading audio for '{track}' by {artist}...")
                            audio_path = download_audio(artist, track)
                            if audio_path:
                                print(f"✓ Audio downloaded to: {audio_path}")
                            else:
                                print("✗ Failed to download audio")
                else:
                    print(f"\n✗ Track '{track_name}'" + (f" by {artist_name}" if artist_name else "") + " not found on Spotify")
                    print("\nTips:")
                    print("- Try different spelling or variations of the track/artist name")
                    print("- Some tracks may not be available in your region")
                    print("- Try searching with just the track name")
                    
    except Exception:
        pass
