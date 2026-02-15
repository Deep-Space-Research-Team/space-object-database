import sqlite3
import json
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, Response

app = FastAPI(title="NASA Space Research API")

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DATA_DIR = BASE_DIR / "data"

DB_DIR.mkdir(exist_ok=True)
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DB_DIR / "space.db"
DATA_FILE = DATA_DIR / "exoplanets.json"

# ==========================================================
# SAFE DATABASE INITIALIZATION
# ==========================================================

@app.on_event("startup")
def initialize_database():
    print("Initializing database...")

    if not DATA_FILE.exists():
        print("⚠ Data file missing. Skipping DB build.")
        return

    try:
        content = DATA_FILE.read_text().strip()

        if not content:
            print("⚠ Data file empty. Skipping DB build.")
            return

        exoplanets = json.loads(content)

        if not isinstance(exoplanets, list):
            print("⚠ Data file invalid format. Skipping DB build.")
            return

    except Exception as e:
        print("⚠ JSON parsing failed:", e)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Always reset table safely
    cur.execute("DROP TABLE IF EXISTS exoplanets")

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

    try:
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
        print("✅ Database initialized successfully.")

    except Exception as e:
        print("⚠ Insert failed:", e)

    finally:
        conn.close()

# ==========================================================
# HEALTH ENDPOINT (for UptimeRobot)
# ==========================================================

@app.get("/health")
def health_get():
    return {"status": "ok"}

@app.head("/health")
def health_head():
    return Response(status_code=200)

# ==========================================================
# ROOT
# ==========================================================

@app.get("/")
def root():
    return {"status": "NASA Space Research API Online"}

@app.head("/")
def root_head():
    return Response(status_code=200)

# ==========================================================
# SAFE QUERY FUNCTION
# ==========================================================

def query_db(query, params=()):
    if not DB_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail="Database not initialized."
        )

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    try:
        cur.execute(query, params)
        rows = cur.fetchall()
        return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()

# ==========================================================
# ROUTES
# ==========================================================

@app.get("/exoplanets")
def get_exoplanets(limit: int = 50):
    return query_db(
        "SELECT * FROM exoplanets LIMIT ?",
        (limit,)
    )

@app.get("/exoplanets/search")
def search_exoplanets(q: str):
    return query_db(
        "SELECT * FROM exoplanets WHERE name LIKE ?",
        (f"%{q}%",)
    )