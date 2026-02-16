import os
import time
import requests
from functools import lru_cache
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import Response

# =====================================================
# CONFIG
# =====================================================

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
# SAFE REQUEST (Retry Logic)
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
# EXOPLANETS (NO DUPLICATES)
# =====================================================

@lru_cache(maxsize=32)
def fetch_exoplanets(limit: int):

    query = """
    select distinct
        pl_name,
        hostname,
        pl_orbper,
        pl_rade,
        pl_bmasse,
        discoverymethod,
        disc_year
    from ps
    order by disc_year desc
    """

    raw = safe_request(EXOPLANET_API, {
        "query": query,
        "format": "json"
    })

    # Remove duplicate planet names manually
    unique_planets = {}
    for p in raw:
        name = p.get("pl_name")
        if name and name not in unique_planets:
            unique_planets[name] = p

    normalized = []

    for p in list(unique_planets.values())[:limit]:

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
# ASTEROIDS (NASA LIVE)
# =====================================================

@app.get("/asteroids/today")
def get_asteroids_today():
    if not NASA_API_KEY:
        raise HTTPException(status_code=500, detail="NASA_API_KEY not set")

    data = safe_request(NEO_API, {
        "api_key": NASA_API_KEY
    })

    near_objects = data.get("near_earth_objects", {})
    results = []

    for date in near_objects:
        for obj in near_objects[date]:
            results.append({
                "name": obj.get("name"),
                "hazardous": obj.get("is_potentially_hazardous_asteroid"),
                "diameter_meters": obj.get("estimated_diameter", {})
                .get("meters", {})
                .get("estimated_diameter_max"),
                "close_approach_date": date
            })

    return results

# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/")
def root():
    return {"status": "NASA Space Research API Online"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.head("/health")
def health_head():
    return Response(status_code=200)
