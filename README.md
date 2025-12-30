# Music Similarity Data Visualization

Fetch and analyze Spotify track data for music similarity visualization.

## Setup

1. **Install dependencies:**
   ```bash
   py -m pip install -r requirements.txt
   ```

2. **Get Spotify API credentials:**
   - Go to https://developer.spotify.com/dashboard
   - Create an app
   - Copy your Client ID and Client Secret

3. **Create `.env` file:**
   ```
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```
   
   Note: The script also supports `CLIENT_ID` and `CLIENT_SECRET` as fallback names.

## Usage

Run the script:
```bash
py main.py
```

The script will:
1. Test your Spotify API connection
2. Ask you to enter either:
   - A Spotify track ID (optional)
   - Or track name (and optionally artist name)
3. Search for the track on Spotify using the `spotipy` library
4. Fetch track metadata, audio features, and audio analysis
5. Extract and display unique attributes representing the track

**Example:**
```
Enter track ID (or press Enter to search by name): 
Enter track name: Blinding Lights
Enter artist name: The Weeknd
```

The script uses `spotipy` library for more reliable searching compared to direct API calls.

## Data Attributes

The script extracts the following unique attributes for each track:

### Basic Info
- Track ID, name, artist, album, release date

### Audio Features
- Danceability, energy, key, loudness, mode
- Speechiness, acousticness, instrumentalness
- Liveness, valence, tempo, time signature
- Duration

### Track Metadata
- Popularity, explicit content flag
- Track number, disc number

### Analysis Confidence
- Tempo, time signature, key, mode confidence scores

