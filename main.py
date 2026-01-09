from fastapi import FastAPI, Query
import httpx

app = FastAPI()

ITUNES_SEARCH_URL = "https://itunes.apple.com/search"

@app.get("/search")
async def search_tracks(
    track_name: str = Query(None, min_length=1, description="Track/song name"),
    artist_name: str = Query(None, min_length=1, description="Artist name"),
    q: str = Query(None, min_length=1, description="General search text (used if track_name/artist_name not provided)"),
    limit: int = Query(25, ge=1, le=200),
    country: str = Query("us", min_length=2, max_length=2),
):
    # Build search term from track_name and artist_name, or use general q
    if track_name or artist_name:
        search_parts = []
        if track_name:
            search_parts.append(track_name.strip())
        if artist_name:
            search_parts.append(artist_name.strip())
        search_term = " ".join(search_parts)
    elif q:
        search_term = q.strip()
    else:
        return {"error": "Must provide either track_name/artist_name or q parameter"}
    
    params = {
        "term": search_term,
        "media": "music",
        "entity": "song",
        "limit": str(limit),
        "country": country.lower(),
    }

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(ITUNES_SEARCH_URL, params=params)
        r.raise_for_status()
        payload = r.json()

    results = payload.get("results", [])

    # Keep only items you want + only tracks with previewUrl
    cleaned = []
    for item in results:
        preview = item.get("previewUrl")
        if not preview:
            continue
        
        # Filter by artist name if provided (case-insensitive match)
        if artist_name:
            item_artist = item.get("artistName", "")
            # Check if the searched artist name is in the track's artist name
            if artist_name.lower() not in item_artist.lower():
                continue
        
        cleaned.append({
            "trackId": item.get("trackId"),
            "trackName": item.get("trackName"),
            "artistName": item.get("artistName"),
            "primaryGenreName": item.get("primaryGenreName"),
            "previewUrl": preview,
        })

    return {"count": len(cleaned), "results": cleaned}