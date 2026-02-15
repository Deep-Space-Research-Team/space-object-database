import sqlite3
from fastapi import FastAPI, HTTPException
from pathlib import Path

app = FastAPI(title="NASA Space Research API")

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "space.db"

# ======================================
# HEALTH CHECK (for UptimeRobot)
# ======================================

@app.api_route("/health", methods=["GET", "HEAD"])
def health():
    return {"status": "ok"}

# ======================================
# ROOT
# ======================================

@app.api_route("/", methods=["GET", "HEAD"])
def root():
    return {"status": "NASA Space Research API Online"}

# ======================================
# SAFE DB QUERY
# ======================================

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

# ======================================
# ROUTES
# ======================================

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
