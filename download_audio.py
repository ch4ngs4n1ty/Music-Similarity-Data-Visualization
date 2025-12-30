"""
Step 1: Download Audio from YouTube

Simple script to download audio files from YouTube for music analysis.
"""
import os
import yt_dlp

def download_audio(artist: str, track_name: str) -> str:
    """
    Download audio from YouTube.
    
    Args:
        artist: Artist name
        track_name: Track name
        
    Returns:
        str: Path to downloaded MP3 file
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
            print(f"Searching YouTube for: {query}...")
            info = ydl.extract_info(f"ytsearch1:{query}", download=True)
            if 'entries' in info:
                filepath = os.path.join(output_dir, f'{artist} - {track_name}.mp3')
                if os.path.exists(filepath):
                    print(f"✅ Downloaded: {filepath}")
                    return filepath
                else:
                    print(f"⚠️  File created but path may differ. Check {output_dir}/")
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

if __name__ == "__main__":
    print("="*60)
    print("Audio Downloader - Step 1")
    print("="*60)
    
    artist = input("Enter artist name: ").strip()
    track = input("Enter track name: ").strip()
    
    if artist and track:
        filepath = download_audio(artist, track)
        if filepath:
            print(f"\n✅ Success! Audio saved to: {filepath}")
    else:
        print("❌ Both artist and track name are required")

