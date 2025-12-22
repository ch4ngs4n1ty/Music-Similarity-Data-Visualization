"""
Database Viewer
===============
Simple script to view what's in your music similarity database.

Shows:
- All artists
- All tracks with their features
- Statistics about your database

How to run:
    python view_database.py
"""

from backend.database import SessionLocal
from backend.models import Artist, Album, Track, AudioFeature

def view_database():
    """Display all data in the database in a readable format."""
    db = SessionLocal()
    
    print("\n" + "="*70)
    print("🎵 MUSIC SIMILARITY DATABASE")
    print("="*70)
    
    # ========== STATISTICS ==========
    artist_count = db.query(Artist).count()
    track_count = db.query(Track).count()
    feature_count = db.query(AudioFeature).count()
    
    print("\n📊 DATABASE STATISTICS:")
    print(f"   Total Artists: {artist_count}")
    print(f"   Total Tracks: {track_count}")
    print(f"   Tracks with Features: {feature_count}")
    
    # ========== ARTISTS ==========
    print("\n" + "-"*70)
    print("👥 ARTISTS:")
    print("-"*70)
    
    artists = db.query(Artist).all()
    if artists:
        for artist in artists:
            # Count tracks by this artist
            track_count = db.query(Track).filter_by(artist_id=artist.id).count()
            print(f"\n{artist.id}. {artist.name}")
            print(f"   Tracks in database: {track_count}")
    else:
        print("   (No artists yet)")
    
    # ========== TRACKS WITH FEATURES ==========
    print("\n" + "-"*70)
    print("🎵 TRACKS WITH AUDIO FEATURES:")
    print("-"*70)
    
    tracks = db.query(Track).all()
    if tracks:
        for track in tracks:
            artist = db.query(Artist).filter_by(id=track.artist_id).first()
            album = db.query(Album).filter_by(id=track.album_id).first()
            features = db.query(AudioFeature).filter_by(track_id=track.id).first()
            
            print(f"\n{track.id}. {track.name}")
            print(f"   Artist: {artist.name}")
            print(f"   Album: {album.name}")
            
            if features:
                print(f"   Audio Features:")
                print(f"      🎼 Tempo: {features.tempo:.1f} BPM")
                print(f"      ⚡ Energy: {features.energy:.3f}")
                print(f"      💃 Danceability: {features.danceability:.3f}")
                print(f"      😊 Valence: {features.valence:.3f}")
            else:
                print(f"   ⚠️  No audio features extracted yet")
    else:
        print("   (No tracks yet)")
        print("\n   👉 Add your first song: python add_song.py \"Song Name\"")
    
    print("\n" + "="*70)
    print("✨ End of database")
    print("="*70 + "\n")
    
    db.close()

if __name__ == "__main__":
    view_database()

