import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "database"
DB_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "space.db"

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# -----------------------
# Create Tables
# -----------------------
cur.execute("""
CREATE TABLE IF NOT EXISTS exoplanets (
    name TEXT,
    host_star TEXT,
    orbital_period_days REAL,
    radius_earth REAL,
    mass_earth REAL,
    discovery_method TEXT,
    discovery_year INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS stars (
    host_star TEXT,
    star_mass REAL,
    star_radius REAL,
    star_temperature REAL
)
""")

# -----------------------
# Insert Exoplanets
# -----------------------
with open(DATA_DIR / "exoplanets.json") as f:
    exoplanets = json.load(f)

cur.executemany("""
INSERT INTO exoplanets VALUES (?,?,?,?,?,?,?)
""", [
    (
        p.get("name"),
        p.get("host_star"),
        p.get("orbital_period_days"),
        p.get("radius_earth"),
        p.get("mass_earth"),
        p.get("discovery_method"),
        p.get("discovery_year"),
    )
    for p in exoplanets
])

# -----------------------
# Insert Stars
# -----------------------
with open(DATA_DIR / "stars.json") as f:
    stars = json.load(f)

cur.executemany("""
INSERT INTO stars VALUES (?,?,?,?)
""", [
    (
        s.get("host_star"),
        s.get("star_mass"),
        s.get("star_radius"),
        s.get("star_temperature"),
    )
    for s in stars
])

# -----------------------
# Indexing (VERY IMPORTANT)
# -----------------------
cur.execute("CREATE INDEX IF NOT EXISTS idx_exoplanet_name ON exoplanets(name)")
cur.execute("CREATE INDEX IF NOT EXISTS idx_host_star ON exoplanets(host_star)")

conn.commit()
conn.close()

print("High-speed research database built successfully!")
