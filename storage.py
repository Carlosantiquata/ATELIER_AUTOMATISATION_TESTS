import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs.db")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            api TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            summary TEXT NOT NULL,
            tests TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def save_run(result: dict):
    init_db()
    conn = _get_conn()
    conn.execute(
        "INSERT INTO runs (api, timestamp, summary, tests) VALUES (?, ?, ?, ?)",
        (
            result.get("api", "Jikan"),
            result.get("timestamp", ""),
            json.dumps(result.get("summary", {})),
            json.dumps(result.get("tests", []))
        )
    )
    conn.commit()
    conn.close()


def list_runs(limit: int = 20):
    init_db()
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        r = dict(row)
        r["summary"] = json.loads(r["summary"])
        r["tests"] = json.loads(r["tests"])
        result.append(r)
    return result
