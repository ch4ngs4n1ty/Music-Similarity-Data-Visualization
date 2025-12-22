"""
Fetch real audio from YouTube and extract features with librosa.
For educational/personal use only.
"""

import os
import yt_dlp
import librosa
import numpy as np
import tempfile

def download_audio_from_youtube(query, output_dir='audio_cache'):
    """Search YouTube and download audio for a song."""
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Configure yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
        'default_search': 'ytsearch1',  # Search and get first result
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Search and download
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            
            if 'entries' in info:
                video = info['entries'][0]
                title = video['title']
                filepath = os.path.join(output_dir, f"{title}.mp3")
                
                return filepath, title
            
    except Exception as e:
        print(f"Error downloading: {e}")
        return None, None

def extract_features_from_file(filepath):
    """Extract audio features from a file using librosa."""
    
    try:
        # Load audio (limit to 30 seconds to match preview length)
        y, sr = librosa.load(filepath, duration=30)
        
        # Extract features
        tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
        
        # Spectral features
        spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
        spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)[0]
        spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)[0]
        
        # Energy
        rms = librosa.feature.rms(y=y)[0]
        
        # Zero crossing rate
        zcr = librosa.feature.zero_crossing_rate(y)[0]
        
        # Chroma features
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        
        # MFCCs
        mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
        
        features = {
            'tempo': float(tempo),
            'energy': float(np.mean(rms)),
            'danceability': float(np.mean(zcr)),  # Proxy
            'valence': float(np.mean(chroma)),  # Proxy
            'spectral_centroid': float(np.mean(spectral_centroid)),
            'spectral_rolloff': float(np.mean(spectral_rolloff)),
            'spectral_bandwidth': float(np.mean(spectral_bandwidth)),
            'mfcc_mean': [float(np.mean(mfcc)) for mfcc in mfccs],
        }
        
        return features
        
    except Exception as e:
        print(f"Error extracting features: {e}")
        return None

def test_youtube_audio():
    """Test downloading and extracting features from YouTube."""
    
    print("🎵 YouTube Audio Feature Extraction")
    print("=" * 60)
    print("\nSearching and downloading audio from YouTube...")
    print("(This uses the first search result)\n")
    
    # Test with a popular song
    query = "Mr. Brightside The Killers"
    print(f"🔍 Searching for: {query}")
    
    filepath, title = download_audio_from_youtube(query)
    
    if filepath and os.path.exists(filepath):
        print(f"✅ Downloaded: {title}")
        print(f"📁 File: {filepath}\n")
        
        print("🔬 Extracting audio features with librosa...")
        features = extract_features_from_file(filepath)
        
        if features:
            print("\n✅ Features extracted successfully!")
            print("=" * 60)
            print("📊 Real Audio Features:")
            print(f"  Tempo: {features['tempo']:.1f} BPM")
            print(f"  Energy: {features['energy']:.4f}")
            print(f"  Danceability (proxy): {features['danceability']:.4f}")
            print(f"  Valence (proxy): {features['valence']:.4f}")
            print(f"  Spectral Centroid: {features['spectral_centroid']:.1f} Hz")
            print(f"  Spectral Rolloff: {features['spectral_rolloff']:.1f} Hz")
            print(f"  Spectral Bandwidth: {features['spectral_bandwidth']:.1f} Hz")
            print("\n🎉 REAL audio features from YouTube!")
            print("\n💡 You can now:")
            print("   1. Search Spotify for track metadata")
            print("   2. Download audio from YouTube")
            print("   3. Extract features with librosa")
            print("   4. Store in your database")
        else:
            print("❌ Failed to extract features")
    else:
        print("❌ Failed to download audio")
        print("\nMake sure you have ffmpeg installed:")
        print("  macOS: brew install ffmpeg")
        print("  Linux: sudo apt-get install ffmpeg")

if __name__ == "__main__":
    test_youtube_audio()

