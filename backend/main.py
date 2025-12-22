"""
FastAPI Backend Server
======================
This is your web API server that will eventually handle requests from the frontend.

What is FastAPI?
- A modern Python framework for building web APIs
- Automatically generates API documentation
- Fast and easy to use

Currently Implemented:
- Health check endpoint (to test if server & database are working)

To Run:
    python backend/main.py
    
Then visit: http://localhost:8000/health
You should see: {"status": "healthy", "database": "connected"}

Future Endpoints to Add:
- POST /search - Search for songs
- GET /track/{id}/similar - Get similar songs
- POST /add_song - Add a new song to database
"""

import sys
import os
# Add parent directory to path so we can import backend modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.database import SessionLocal

# Create the FastAPI app
app = FastAPI(title="Music Similarity API")

# CORS (Cross-Origin Resource Sharing)
# This allows your frontend (HTML/JS) to talk to your backend API
# "*" means allow requests from any origin (fine for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend URL
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

@app.get("/health")
def health_check():
    """
    Health Check Endpoint
    =====================
    Tests if the API server and database are working.
    
    Returns:
        - {"status": "healthy", "database": "connected"} if everything works
        - {"status": "unhealthy", "error": "..."} if there's a problem
    
    Example:
        Visit: http://localhost:8000/health
    """
    try:
        # Try to connect to database and run a simple query
        db = SessionLocal()
        db.execute("SELECT 1")  # Simple test query
        db.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

# This runs when you execute: python backend/main.py
if __name__ == "__main__":
    import uvicorn
    # Start the server on http://0.0.0.0:8000
    # 0.0.0.0 means accessible from any network interface
    uvicorn.run(app, host="0.0.0.0", port=8000)
