-- schema.sql
-- The logger.py script creates this automatically via init_db().
-- This file is here for reference and documentation purposes.

CREATE TABLE IF NOT EXISTS metrics (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp         TEXT NOT NULL,          -- ISO 8601 UTC timestamp
    instance_id       TEXT NOT NULL,          -- AWS EC2 instance ID (e.g. i-0abc123)
    cpu_utilization   REAL,                   -- % CPU used (0-100)
    network_in_bytes  REAL,                   -- bytes received in period
    network_out_bytes REAL,                   -- bytes sent in period
    status            TEXT                    -- 'ok' or error description
);

-- Index for fast time-range queries
CREATE INDEX IF NOT EXISTS idx_timestamp ON metrics (timestamp);

-- Useful queries for analysis:

-- Average CPU over all time
-- SELECT ROUND(AVG(cpu_utilization), 2) AS avg_cpu FROM metrics;

-- Readings where CPU exceeded 80%
-- SELECT timestamp, cpu_utilization FROM metrics WHERE cpu_utilization > 80 ORDER BY timestamp DESC;

-- Hourly average CPU (useful for Tableau)
-- SELECT
--     strftime('%Y-%m-%d %H:00', timestamp) AS hour,
--     ROUND(AVG(cpu_utilization), 2) AS avg_cpu
-- FROM metrics
-- GROUP BY hour
-- ORDER BY hour ASC;
