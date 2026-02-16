import os
import time
import requests
from functools import lru_cache
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response

NASA_API_KEY = os.getenv("NASA_API_KEY")

EXOPLANET_API = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
NEO_API = "https://api.nasa.gov/neo/rest/v1/feed"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

app = FastAPI(title="NASA Live Space API")

# =====================================================
# CLASSIFICATION ENGINE
# =====================================================

def classify_planet(radius, mass, orbital_period):
    if radius is None:
        return "Unknown"

    try:
        radius = float(radius)
    except:
        return "Unknown"

    if radius < 1.25:
        return "Rocky"

    if 1.25 <= radius <= 2:
        return "Super Earth"

    if 2 < radius <= 4:
        return "Mini Neptune"

    if radius > 4:
        if orbital_period and orbital_period < 10:
            return "Hot Jupiter"
        return "Gas Giant"

    return "Unknown"

# =====================================================
# SAFE REQUEST
# =====================================================

def safe_request(url, params):
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.RequestException:
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)
                continue
            raise HTTPException(status_code=502, detail="External API error")

# =====================================================
# EXOPLANETS
# =====================================================

@lru_cache(maxsize=32)
def fetch_exoplanets(limit: int):
    query = f"""
    select top {limit}
    pl_name, hostname, pl_orbper,
    pl_rade, pl_bmasse,
    discoverymethod, disc_year
    from ps
    """

    raw = safe_request(EXOPLANET_API, {
        "query": query,
        "format": "json"
    })

    normalized = []

    for p in raw:
        radius = p.get("pl_rade")
        mass = p.get("pl_bmasse")
        orbital = p.get("pl_orbper")

        classification = classify_planet(radius, mass, orbital)

        normalized.append({
            "name": p.get("pl_name"),
            "host_star": p.get("hostname"),
            "orbital_period_days": orbital,
            "radius_earth": radius,
            "mass_earth": mass,
            "discovery_method": p.get("discoverymethod"),
            "discovery_year": p.get("disc_year"),
            "classification": classification
        })

    return normalized

@app.get("/exoplanets")
def get_exoplanets(limit: int = Query(20, ge=1, le=200)):
    return fetch_exoplanets(limit)

# =====================================================
# HEALTH
# =====================================================

@app.get("/health")
def health():
    return {"status": "ok"}

@app.head("/health")
def health_head():
    return Response(status_code=200)
