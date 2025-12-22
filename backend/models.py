"""
Database Models (Tables)
=========================
This file defines the structure of our database tables.

Think of each class as a table in a spreadsheet:
- Each class = one table
- Each Column = one column in that table
- ForeignKey = links to another table (like a reference)

Our Database Structure:
    Artist → Album → Track → AudioFeature
           ↓         ↓
         Album    Embedding
                     ↓
                  Neighbor
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey
from backend.database import Base

# ============================================================================
# ARTIST TABLE
# ============================================================================
class Artist(Base):
    """
    Stores information about music artists.
    
    Example row:
        id=1, name="The Weeknd", spotify_id="1Xyo4u8uXC1ZmMpatF05PJ"
    """
    __tablename__ = "artists"
    
    id = Column(Integer, primary_key=True)  # Unique ID for each artist
    name = Column(String, nullable=False, index=True)  # Artist name (indexed for fast search)
    spotify_id = Column(String)  # Spotify's ID for this artist

# ============================================================================
# ALBUM TABLE
# ============================================================================
class Album(Base):
    """
    Stores information about albums.
    
    Example row:
        id=1, name="After Hours", artist_id=1, spotify_id="4yP0hdKOZPNshxUOjY0cZj"
    """
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True)  # Unique ID for each album
    name = Column(String, nullable=False)  # Album name
    artist_id = Column(Integer, ForeignKey("artists.id"))  # Links to Artist table
    spotify_id = Column(String)  # Spotify's ID for this album

# ============================================================================
# TRACK TABLE
# ============================================================================
class Track(Base):
    """
    Stores information about individual songs/tracks.
    
    Example row:
        id=1, name="Blinding Lights", artist_id=1, album_id=1, 
        spotify_id="0VjIjW4GlUZAMYd2vXMi3b", preview_url="https://..."
    """
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True)  # Unique ID for each track
    name = Column(String, nullable=False, index=True)  # Track name (indexed for search)
    artist_id = Column(Integer, ForeignKey("artists.id"))  # Links to Artist
    album_id = Column(Integer, ForeignKey("albums.id"))  # Links to Album
    spotify_id = Column(String)  # Spotify's ID for this track
    preview_url = Column(String)  # URL to 30-second audio preview (if available)

# ============================================================================
# AUDIO FEATURE TABLE
# ============================================================================
class AudioFeature(Base):
    """
    Stores extracted audio features for each track.
    These features are used to calculate song similarity.
    
    Features explained:
    - energy: How energetic/intense the song is (0.0 to 1.0)
    - valence: How positive/happy the song sounds (0.0 to 1.0)
    - tempo: Speed of the song in Beats Per Minute (BPM)
    - danceability: How suitable for dancing (0.0 to 1.0)
    
    Example row:
        id=1, track_id=1, energy=0.145, valence=0.484, 
        tempo=103.4, danceability=0.037
    """
    __tablename__ = "audio_features"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), index=True)  # Links to Track
    energy = Column(Float)  # Energy level (0-1)
    valence = Column(Float)  # Mood/positivity (0-1)
    tempo = Column(Float)  # Speed in BPM
    danceability = Column(Float)  # Danceability score (0-1)

# ============================================================================
# EMBEDDING TABLE (For Future Use)
# ============================================================================
class Embedding(Base):
    """
    Stores 2D coordinates for visualizing songs on a map.
    UMAP reduces complex audio features to just X,Y coordinates.
    
    This allows us to plot songs on a 2D scatter plot where:
    - Similar songs appear close together
    - Different songs appear far apart
    
    (Not currently used - will be needed for Power BI visualization)
    """
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), index=True)
    umap_x = Column(Float)  # X coordinate on the map
    umap_y = Column(Float)  # Y coordinate on the map

# ============================================================================
# NEIGHBOR TABLE (For Future Use)
# ============================================================================
class Neighbor(Base):
    """
    Pre-calculated similarity relationships between songs.
    Stores which songs are most similar to each other.
    
    Example row:
        id=1, track_id=1, neighbor_track_id=2, similarity_score=0.989
        
    This means Track #1 is 98.9% similar to Track #2
    
    (Not currently used - calculated on-the-fly in add_song.py)
    """
    __tablename__ = "neighbors"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), index=True)  # The main track
    neighbor_track_id = Column(Integer, ForeignKey("tracks.id"))  # The similar track
    similarity_score = Column(Float)  # How similar they are (0.0 to 1.0)

