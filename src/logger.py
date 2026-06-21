"""
logger.py
---------
Handles all database operations: initialising the schema,
inserting metric rows, and basic retrieval.
"""

import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import DB_PATH


def get_connection():
    """Returns a connection to the SQLite metrics database."""
    return sqlite3.connect(DB_PATH)


def init_db():
    """
    Creates the metrics table if it doesn't exist.
    Safe to call on every startup.
    """
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp       TEXT NOT NULL,
                instance_id     TEXT NOT NULL,
                cpu_utilization REAL,
                network_in_bytes REAL,
                network_out_bytes REAL,
                status          TEXT
            )
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp
            ON metrics (timestamp)
        """)
        conn.commit()
    print(f"[+] Database initialised at: {DB_PATH}")


def log_metric(metrics: dict):
    """Inserts one metric reading into the database."""
    with get_connection() as conn:
        conn.execute("""
            INSERT INTO metrics
                (timestamp, instance_id, cpu_utilization,
                 network_in_bytes, network_out_bytes, status)
            VALUES
                (:timestamp, :instance_id, :cpu_utilization,
                 :network_in_bytes, :network_out_bytes, :status)
        """, metrics)
        conn.commit()


def fetch_recent(limit=20):
    """Returns the most recent N metric rows."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.execute("""
            SELECT * FROM metrics
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


def fetch_summary(instance_id):
    """Returns aggregate stats for a given instance."""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        
        # 1. Get the basic stats and uptime count
        cursor = conn.execute("""
            SELECT
                COUNT(*)                        AS total_readings,
                ROUND(AVG(cpu_utilization), 2)  AS avg_cpu,
                ROUND(MAX(cpu_utilization), 2)  AS peak_cpu,
                ROUND(MIN(cpu_utilization), 2)  AS min_cpu,
                MIN(timestamp)                  AS first_reading,
                MAX(timestamp)                  AS last_reading,
                SUM(CASE WHEN status = 'ok' THEN 1 ELSE 0 END) AS ok_readings
            FROM metrics
            WHERE instance_id = ?
        """, (instance_id,))
        summary = dict(cursor.fetchone())
        
        # 2. Get the exact time of the peak CPU
        cursor = conn.execute("""
            SELECT timestamp 
            FROM metrics 
            WHERE instance_id = ? AND cpu_utilization = ?
            LIMIT 1
        """, (instance_id, summary['peak_cpu']))
        peak_row = cursor.fetchone()
        summary['peak_time'] = peak_row['timestamp'] if peak_row else "N/A"
        
        # 3. Calculate Uptime Percentage
        if summary['total_readings'] > 0:
            uptime = (summary['ok_readings'] / summary['total_readings']) * 100
            summary['uptime_pct'] = round(uptime, 2)
        else:
            summary['uptime_pct'] = 0.0
            
        return summary


if __name__ == "__main__":
    # Quick test: initialise DB and insert a dummy row
    init_db()
    test_metric = {
        "timestamp": "2025-07-01T12:00:00+00:00",
        "instance_id": "i-test123",
        "cpu_utilization": 12.5,
        "network_in_bytes": 204800.0,
        "network_out_bytes": 102400.0,
        "status": "ok"
    }
    log_metric(test_metric)
    print("[+] Test row inserted.")
    rows = fetch_recent(5)
    for row in rows:
        print(row)
