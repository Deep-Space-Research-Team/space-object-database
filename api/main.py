import os
import time
import requests
from functools import lru_cache
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response

# ==========================================================
# CONFIG
# ==========================================================

NASA_API_KEY = os.getenv("NASA_API_KEY")
EXOPLANET_API = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
NEO_API = "https://api.nasa.gov/neo/rest/v1/feed"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

if not NASA_API_KEY:
    raise RuntimeError("NASA_API_KEY environment variable not set")

app = FastAPI(title="NASA Live Space API")

# ==========================================================
# HEALTH
# ==========================================================

@app.get("/health")
def health():
    return {"status": "ok"}

@app.head("/health")
def health_head():
    return Response(status_code=200)

# ==========================================================
# DEBUG ROUTE (Remove later if needed)
# ==========================================================

@app.get("/routes")
def list_routes():
    return [route.path for route in app.routes]

# ==========================================================
# SAFE REQUEST FUNCTION
# ==========================================================

def safe_request(url, params):
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                url,
                params=params,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            raise HTTPException(
                status_code=502,
                detail=f"External API error: {str(e)}"
            )

# ==========================================================
# EXOPLANETS (LIVE)
# ==========================================================

@lru_cache(maxsize=32)
def fetch_exoplanets(limit: int):
    query = f"""
    select top {limit}
    pl_name, hostname, pl_orbper, pl_rade,
    pl_bmasse, discoverymethod, disc_year
    from ps
    """

    return safe_request(EXOPLANET_API, {
        "query": query,
        "format": "json"
    })

@app.get("/exoplanets")
def get_exoplanets(limit: int = Query(20, ge=1, le=200)):
    return fetch_exoplanets(limit)

# ==========================================================
# ASTEROIDS (LIVE NEO FEED)
# ==========================================================

@lru_cache(maxsize=4)
def fetch_asteroids():
    return safe_request(NEO_API, {
        "api_key": NASA_API_KEY
    })

@app.get("/asteroids/today")
def get_asteroids():
    return fetch_asteroids()

# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def root():
    return {
        "status": "NASA Live Space API Online",
        "endpoints": [
            "/health",
            "/exoplanets?limit=20",
            "/asteroids/today"
        ]
    }
