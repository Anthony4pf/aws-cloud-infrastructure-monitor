"""
test_monitor.py
---------------
Basic tests for the logger and reporter modules.
Run with: python -m pytest tests/
"""

import os
import sys
import sqlite3
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Use a separate test database so tests don't pollute real data
os.environ["DB_PATH"] = "test_metrics.db"

from src.logger import init_db, log_metric, fetch_recent, fetch_summary


@pytest.fixture(autouse=True)
def clean_db():
    """Creates a fresh test database before each test, removes it after."""
    init_db()
    yield
    if os.path.exists("test_metrics.db"):
        os.remove("test_metrics.db")


def sample_metric(cpu=25.0, status="ok"):
    return {
        "timestamp": "2025-07-01T12:00:00+00:00",
        "instance_id": "i-test123",
        "cpu_utilization": cpu,
        "network_in_bytes": 204800.0,
        "network_out_bytes": 102400.0,
        "status": status
    }


def test_log_and_retrieve():
    """Logged metric should appear in fetch_recent results."""
    log_metric(sample_metric())
    rows = fetch_recent(5)
    assert len(rows) == 1
    assert rows[0]["instance_id"] == "i-test123"
    assert rows[0]["cpu_utilization"] == 25.0


def test_multiple_readings():
    """fetch_recent should return rows in descending timestamp order."""
    log_metric(sample_metric(cpu=10.0))
    log_metric({**sample_metric(cpu=50.0), "timestamp": "2025-07-01T13:00:00+00:00"})
    rows = fetch_recent(10)
    assert len(rows) == 2
    # Most recent first
    assert rows[0]["cpu_utilization"] == 50.0


def test_summary_averages():
    """fetch_summary should compute correct averages."""
    log_metric(sample_metric(cpu=20.0))
    log_metric({**sample_metric(cpu=40.0), "timestamp": "2025-07-01T13:00:00+00:00"})
    summary = fetch_summary("i-test123")
    assert summary["total_readings"] == 2
    assert summary["avg_cpu"] == 30.0
    assert summary["peak_cpu"] == 40.0
    assert summary["min_cpu"] == 20.0


def test_null_cpu_handled():
    """Logger should handle None CPU values without crashing."""
    metric = sample_metric()
    metric["cpu_utilization"] = None
    log_metric(metric)
    rows = fetch_recent(1)
    assert rows[0]["cpu_utilization"] is None


def test_status_logged_correctly():
    """Non-ok status strings should be stored accurately."""
    log_metric(sample_metric(status="system:impaired instance:ok"))
    rows = fetch_recent(1)
    assert rows[0]["status"] == "system:impaired instance:ok"
