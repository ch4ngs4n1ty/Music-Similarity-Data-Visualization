import os
import requests
import librosa
import numpy as np
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import tempfile

load_dotenv()

def extract_features_from_preview(preview_url):
    """Download preview and extract audio features using librosa."""
    
    if not preview_url:
        return None
    
    try:
        # Download the preview
        response = requests.get(preview_url, timeout=10)
        response.raise_for_status()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as tmp_file:
            tmp_file.write(response.content)
            tmp_path = tmp_file.name
        
        # Load audio with librosa
        y, sr = librosa.load(tmp_path, duration=30)
        
        # Extract features
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        
        # Spectral features
        spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        
        # Zero crossing rate (energy proxy)
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # RMS energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Chroma features (harmony)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # MFCC (timbre)
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        # Aggregate features
        features = {
            'tempo': float(tempo),
            'energy': float(np.mean(rms)),
            'danceability': float(np.mean(zcr)),  # Proxy
            'valence': float(np.mean(chroma)),  # Proxy for mood
            'spectral_centroid': float(np.mean(spectral_centroids)),
            'spectral_rolloff': float(np.mean(spectral_rolloff)),
            'mfcc_mean': [float(np.mean(mfcc)) for mfcc in mfccs],
        }
        
        # Cleanup
        os.remove(tmp_path)
        
        return features
        
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None

def test_with_spotify():
    """Test feature extraction with Spotify tracks."""
    
    client_id = os.getenv('SPOTIFY_CLIENT_ID')
    client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
    
    auth_manager = SpotifyClientCredentials(
        client_id=client_id,
        client_secret=client_secret
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)
    
    # Search for tracks with previews (try multiple genres)
    print("🔍 Searching for tracks with preview URLs...\n")
    
    for query in ['year:2020-2024 genre:pop', 'Drake', 'Ed Sheeran', 'The Weeknd']:
        print(f"Trying search: {query}")
        results = sp.search(q=query, type='track', limit=50)
        
        # Check if any have previews
        tracks_with_previews = [t for t in results['tracks']['items'] if t.get('preview_url')]
        if tracks_with_previews:
            print(f"✅ Found {len(tracks_with_previews)} tracks with previews!\n")
            results = {'tracks': {'items': tracks_with_previews}}
            break
    else:
        print("❌ No tracks with preview URLs found after trying multiple searches.")
        return
    
    found = False
    for track in results['tracks']['items']:
        preview_url = track.get('preview_url')
        
        if preview_url:
            found = True
            artist = track['artists'][0]['name']
            name = track['name']
            
            print(f"🎵 Track: {name} by {artist}")
            print(f"📍 Preview URL: {preview_url[:50]}...")
            print("\n🔬 Extracting audio features...")
            
            features = extract_features_from_preview(preview_url)
            
            if features:
                print("\n✅ Features extracted successfully:")
                print(f"  Tempo: {features['tempo']:.1f} BPM")
                print(f"  Energy: {features['energy']:.3f}")
                print(f"  Danceability (proxy): {features['danceability']:.3f}")
                print(f"  Valence (proxy): {features['valence']:.3f}")
                print(f"  Spectral Centroid: {features['spectral_centroid']:.1f} Hz")
                print(f"  Spectral Rolloff: {features['spectral_rolloff']:.1f} Hz")
                print("\n🎉 Librosa feature extraction is working!")
            else:
                print("❌ Failed to extract features")
            
            break
    
    if not found:
        print("❌ No tracks with preview URLs found. Try a different search term.")

if __name__ == "__main__":
    test_with_spotify()

