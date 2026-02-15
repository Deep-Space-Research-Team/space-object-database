from fastapi import FastAPI, Query
import sqlite3
from pathlib import Path

app = FastAPI(title="NASA Space Research API")

DB_PATH = Path(__file__).resolve().parent.parent / "database" / "space.db"

def query_db(query, params=()):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

@app.get("/")
def root():
    return {"status": "NASA Space Research API Online"}

@app.get("/exoplanets")
def get_exoplanets(
    limit: int = 50,
    offset: int = 0
):
    return query_db(
        "SELECT * FROM exoplanets LIMIT ? OFFSET ?",
        (limit, offset)
    )

@app.get("/exoplanets/search")
def search_exoplanets(q: str):
    return query_db(
        "SELECT * FROM exoplanets WHERE name LIKE ?",
        (f"%{q}%",)
    )

@app.get("/exoplanets/filter")
def filter_exoplanets(
    min_mass: float = Query(None),
    max_mass: float = Query(None)
):
    query = "SELECT * FROM exoplanets WHERE 1=1"
    params = []

    if min_mass is not None:
        query += " AND mass_earth >= ?"
        params.append(min_mass)

    if max_mass is not None:
        query += " AND mass_earth <= ?"
        params.append(max_mass)

    return query_db(query, params)
