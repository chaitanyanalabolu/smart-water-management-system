"""
backend_api.py
----------------
Data & Application layer for the Smart Water Monitoring System.

A small FastAPI service that:
  1. Ingests readings published by household edge devices (normally
     received via an MQTT bridge that forwards to this HTTP endpoint,
     or called directly by devices that speak HTTPS instead of MQTT).
  2. Stores readings in a lightweight local database (SQLite here -
     swap for InfluxDB/PostgreSQL in production; the query layer below
     is written in plain SQL so the swap is a connection-string change).
  3. Runs the AI/data-science anomaly check (see ai_anomaly_detection.py)
     on each new reading and raises an alert if needed.
  4. Exposes read endpoints that power the household and authority
     dashboards shown in the presentation.

Run locally:
    pip install fastapi uvicorn
    uvicorn backend_api:app --reload

Then, e.g.:
    curl -X POST localhost:8000/readings -H "Content-Type: application/json" \
      -d '{"household_id":"H001","ward":"Ward 1","flow_litres":12.4,
           "cumulative_daily_litres":48.9,"daily_limit_litres":166}'
"""
from datetime import datetime, date
from typing import Optional, List

import sqlite3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

DB_PATH = "swm.db"
app = FastAPI(title="Smart Water Monitoring API")


# ---------------------- Schema ----------------------
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_id TEXT NOT NULL,
            ward TEXT NOT NULL,
            ts TEXT NOT NULL,
            flow_litres REAL NOT NULL,
            cumulative_daily_litres REAL NOT NULL,
            daily_limit_litres REAL NOT NULL,
            is_anomaly INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            household_id TEXT NOT NULL,
            ward TEXT NOT NULL,
            ts TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            detail TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------------------- Request / response models ----------------------
class ReadingIn(BaseModel):
    household_id: str
    ward: str
    flow_litres: float
    cumulative_daily_litres: float
    daily_limit_litres: float
    timestamp: Optional[str] = None  # ISO string; server time used if omitted


class AlertOut(BaseModel):
    household_id: str
    ward: str
    ts: str
    alert_type: str
    detail: Optional[str] = None


# ---------------------- AI layer hook ----------------------
def score_for_anomaly(household_id: str, flow_litres: float, hour: int) -> bool:
    """
    Lightweight rolling-baseline check used at ingest time so alerts are
    near-instant. This mirrors the overnight-leak rule demonstrated in
    ai_anomaly_detection.py: continuous flow between 01:00-05:00 above a
    small "no one should be using water right now" threshold is flagged.
    The heavier Isolation-Forest model in ai_anomaly_detection.py is run
    as a periodic batch job for the pattern-level anomalies this
    fast-path check can't catch.
    """
    NIGHT_HOURS = range(1, 6)
    NIGHT_LEAK_THRESHOLD_L = 3.5  # litres in a single hourly interval, 01:00-05:00
    return hour in NIGHT_HOURS and flow_litres >= NIGHT_LEAK_THRESHOLD_L


# ---------------------- Ingest endpoint ----------------------
@app.post("/readings")
def ingest_reading(reading: ReadingIn):
    ts = reading.timestamp or datetime.utcnow().isoformat()
    hour = datetime.fromisoformat(ts).hour

    anomaly = score_for_anomaly(reading.household_id, reading.flow_litres, hour)
    limit_breached = reading.cumulative_daily_litres >= reading.daily_limit_litres

    conn = get_db()
    conn.execute(
        """INSERT INTO readings
           (household_id, ward, ts, flow_litres, cumulative_daily_litres,
            daily_limit_litres, is_anomaly)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (reading.household_id, reading.ward, ts, reading.flow_litres,
         reading.cumulative_daily_litres, reading.daily_limit_litres, int(anomaly))
    )

    if anomaly:
        conn.execute(
            """INSERT INTO alerts (household_id, ward, ts, alert_type, detail)
               VALUES (?, ?, ?, ?, ?)""",
            (reading.household_id, reading.ward, ts, "POSSIBLE_LEAK",
             f"{reading.flow_litres:.1f} L flowed between 01:00-05:00")
        )
    if limit_breached:
        conn.execute(
            """INSERT INTO alerts (household_id, ward, ts, alert_type, detail)
               VALUES (?, ?, ?, ?, ?)""",
            (reading.household_id, reading.ward, ts, "DAILY_LIMIT_EXCEEDED",
             f"{reading.cumulative_daily_litres:.1f} / {reading.daily_limit_litres:.0f} L")
        )

    conn.commit()
    conn.close()
    return {"stored": True, "anomaly_flagged": anomaly, "limit_breached": limit_breached}


# ---------------------- Household dashboard endpoint ----------------------
@app.get("/households/{household_id}/today")
def household_today(household_id: str):
    today = date.today().isoformat()
    conn = get_db()
    row = conn.execute(
        """SELECT SUM(flow_litres) AS total, MAX(daily_limit_litres) AS limit_l
           FROM readings WHERE household_id = ? AND ts LIKE ?""",
        (household_id, f"{today}%")
    ).fetchone()
    conn.close()
    if row is None or row["total"] is None:
        raise HTTPException(status_code=404, detail="No readings today for this household")
    return {
        "household_id": household_id,
        "date": today,
        "usage_litres": round(row["total"], 1),
        "daily_limit_litres": row["limit_l"],
        "pct_of_limit": round(100 * row["total"] / row["limit_l"], 1),
    }


# ---------------------- Authority dashboard endpoint ----------------------
@app.get("/wards/summary")
def ward_summary():
    today = date.today().isoformat()
    conn = get_db()
    rows = conn.execute(
        """SELECT ward, SUM(flow_litres) AS total_litres, COUNT(DISTINCT household_id) AS households
           FROM readings WHERE ts LIKE ? GROUP BY ward ORDER BY ward""",
        (f"{today}%",)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/alerts/recent", response_model=List[AlertOut])
def recent_alerts(limit: int = 20):
    conn = get_db()
    rows = conn.execute(
        "SELECT household_id, ward, ts, alert_type, detail FROM alerts ORDER BY ts DESC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.get("/health")
def health():
    return {"status": "ok", "time": datetime.utcnow().isoformat()}
