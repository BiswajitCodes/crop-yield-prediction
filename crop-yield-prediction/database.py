"""SQLite prediction history. Keeps the original `predictions` table and adds columns safely."""
from __future__ import annotations

import sqlite3
from datetime import datetime

import config

_NEW_COLUMNS = {
    "production": "REAL",
    "fertilizer_rate": "REAL",   # kg/ha as entered
    "pesticide_rate": "REAL",    # kg/ha as entered
    "yield_unit": "TEXT",
    "production_unit": "TEXT",
}


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                crop TEXT NOT NULL,
                state TEXT NOT NULL,
                season TEXT NOT NULL,
                crop_year INTEGER NOT NULL,
                area REAL NOT NULL,
                annual_rainfall REAL NOT NULL,
                fertilizer REAL NOT NULL,
                pesticide REAL NOT NULL,
                predicted_yield REAL NOT NULL
            )""")
        existing = {r["name"] for r in conn.execute("PRAGMA table_info(predictions)")}
        for col, typ in _NEW_COLUMNS.items():
            if col not in existing:
                conn.execute(f"ALTER TABLE predictions ADD COLUMN {col} {typ}")
        # Back-fill rows saved by the earlier app version using exact arithmetic on stored values.
        conn.execute("UPDATE predictions SET production = predicted_yield * area WHERE production IS NULL")
        conn.execute("UPDATE predictions SET fertilizer_rate = fertilizer / area WHERE fertilizer_rate IS NULL AND area > 0")
        conn.execute("UPDATE predictions SET pesticide_rate = pesticide / area WHERE pesticide_rate IS NULL AND area > 0")
        conn.commit()


def save_prediction(record: dict) -> int:
    """record keys: Crop, State, Season, Crop_Year, Area, Annual_Rainfall, Fertilizer, Pesticide,
    predicted_yield (+ optional production, fertilizer_rate, pesticide_rate, yield_unit, production_unit)."""
    area = float(record["Area"])
    y = float(record["predicted_yield"])
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO predictions
               (created_at, crop, state, season, crop_year, area, annual_rainfall, fertilizer, pesticide,
                predicted_yield, production, fertilizer_rate, pesticide_rate, yield_unit, production_unit)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (datetime.now().isoformat(timespec="seconds"), record["Crop"], record["State"], record["Season"],
             int(record["Crop_Year"]), area, float(record["Annual_Rainfall"]), float(record["Fertilizer"]),
             float(record["Pesticide"]), y, float(record.get("production", y * area)),
             record.get("fertilizer_rate"), record.get("pesticide_rate"),
             record.get("yield_unit"), record.get("production_unit")),
        )
        conn.commit()
        return int(cur.lastrowid)


def get_predictions(limit: int = 5000) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM predictions ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
    return [dict(r) for r in rows]


def delete_predictions(ids: list[int]) -> int:
    ids = [int(i) for i in ids]
    if not ids:
        return 0
    with get_connection() as conn:
        cur = conn.execute(f"DELETE FROM predictions WHERE id IN ({','.join('?' * len(ids))})", ids)
        conn.commit()
        return cur.rowcount


def clear_predictions() -> int:
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM predictions")
        conn.commit()
        return cur.rowcount
