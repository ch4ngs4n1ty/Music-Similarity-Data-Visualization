from sqlalchemy import Column, Integer, String, Float, ForeignKey
from backend.database import Base

class Artist(Base):
    __tablename__ = "artists"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    spotify_id = Column(String)

class Album(Base):
    __tablename__ = "albums"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    spotify_id = Column(String)

class Track(Base):
    __tablename__ = "tracks"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    artist_id = Column(Integer, ForeignKey("artists.id"))
    album_id = Column(Integer, ForeignKey("albums.id"))
    spotify_id = Column(String)
    preview_url = Column(String)

class AudioFeature(Base):
    __tablename__ = "audio_features"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), index=True)
    energy = Column(Float)
    valence = Column(Float)
    tempo = Column(Float)
    danceability = Column(Float)

class Embedding(Base):
    __tablename__ = "embeddings"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), index=True)
    umap_x = Column(Float)
    umap_y = Column(Float)

class Neighbor(Base):
    __tablename__ = "neighbors"
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey("tracks.id"), index=True)
    neighbor_track_id = Column(Integer, ForeignKey("tracks.id"))
    similarity_score = Column(Float)

