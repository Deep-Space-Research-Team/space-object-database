import sqlite3
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DB_DIR = BASE_DIR / "database"

DB_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "space.db"
DATA_FILE = DATA_DIR / "exoplanets.json"

if not DATA_FILE.exists():
    print("Data file missing.")
    exit()

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

# Drop table if exists (prevents corruption)
cur.execute("DROP TABLE IF EXISTS exoplanets")

# Create table
cur.execute("""
CREATE TABLE exoplanets (
    name TEXT,
    host_star TEXT,
    orbital_period_days REAL,
    radius_earth REAL,
    mass_earth REAL,
    discovery_method TEXT,
    discovery_year INTEGER
)
""")

with open(DATA_FILE) as f:
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

conn.commit()
conn.close()

print("Database rebuilt successfully.")