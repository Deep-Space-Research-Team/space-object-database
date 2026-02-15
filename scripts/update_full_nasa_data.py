import requests
import pandas as pd
import json
from pathlib import Path
from datetime import datetime, timedelta

# ----------------------------
# Setup directories
# ----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
SOLAR_DIR = DATA_DIR / "solar_system"

DATA_DIR.mkdir(exist_ok=True)
SOLAR_DIR.mkdir(exist_ok=True)

API_KEY = "DEMO_KEY"  # Replace with your NASA API key

# ----------------------------
# Helper: Safe request
# ----------------------------
def safe_get_json(url):
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Request failed: {e}")
        return None

# ----------------------------
# 1️⃣ NASA Exoplanet Archive (Explicit TAP query)
# ----------------------------
print("Fetching Exoplanet Archive (controlled columns)...")

exo_url = (
    "https://exoplanetarchive.ipac.caltech.edu/TAP/sync?"
    "query=select+pl_name,hostname,pl_orbper,pl_rade,pl_bmasse,"
    "st_mass,st_rad,st_teff,discoverymethod,disc_year+from+pscomppars"
    "&format=csv"
)

try:
    exo_df = pd.read_csv(exo_url)

    exo_df.rename(columns={
        "pl_name": "name",
        "hostname": "host_star",
        "pl_orbper": "orbital_period_days",
        "pl_rade": "radius_earth",
        "pl_bmasse": "mass_earth",
        "st_mass": "star_mass",
        "st_rad": "star_radius",
        "st_teff": "star_temperature",
        "discoverymethod": "discovery_method",
        "disc_year": "discovery_year"
    }, inplace=True)

    exo_df.to_json(DATA_DIR / "exoplanets.json", orient="records", indent=2)
    print(f"Exoplanets saved: {len(exo_df)} entries")

    # Extract Host Stars safely
    print("Extracting host stars...")
    star_columns = ["host_star", "star_mass", "star_radius", "star_temperature"]
    available = [c for c in star_columns if c in exo_df.columns]

    if available:
        stars = exo_df[available].drop_duplicates()
        stars.to_json(DATA_DIR / "stars.json", orient="records", indent=2)
        print(f"Stars saved: {len(stars)} entries")
    else:
        print("Star columns missing — skipped.")

except Exception as e:
    print("Exoplanet fetch failed:", e)

# ----------------------------
# 2️⃣ JPL Small-Body Database
# ----------------------------
print("Fetching SBDB asteroid data...")

sbdb_url = "https://ssd-api.jpl.nasa.gov/sbdb_query.api?fields=full_name,a,e,i,diameter"
sbdb_data = safe_get_json(sbdb_url)

if sbdb_data:
    with open(DATA_DIR / "asteroids.json", "w") as f:
        json.dump(sbdb_data, f, indent=2)
    print("Asteroid data saved.")
else:
    print("Asteroid fetch failed.")

# ----------------------------
# 3️⃣ NASA NeoWs (Dynamic Dates)
# ----------------------------
print("Fetching Near-Earth Object feed...")

today = datetime.utcnow()
start = today.strftime("%Y-%m-%d")
end = (today + timedelta(days=7)).strftime("%Y-%m-%d")

neo_url = (
    f"https://api.nasa.gov/neo/rest/v1/feed?"
    f"start_date={start}&end_date={end}&api_key={API_KEY}"
)

neo_data = safe_get_json(neo_url)

if neo_data:
    with open(DATA_DIR / "neows_feed.json", "w") as f:
        json.dump(neo_data, f, indent=2)
    print("NEO feed saved.")
else:
    print("NEO fetch failed.")

# ----------------------------
# 4️⃣ Solar System Planets
# ----------------------------
print("Saving Solar System planets...")

planets = [
    {"name": "Mercury"},
    {"name": "Venus"},
    {"name": "Earth"},
    {"name": "Mars"},
    {"name": "Jupiter"},
    {"name": "Saturn"},
    {"name": "Uranus"},
    {"name": "Neptune"}
]

with open(SOLAR_DIR / "planets.json", "w") as f:
    json.dump(planets, f, indent=2)

print("Solar system data saved.")

print("All NASA data updated successfully!")
