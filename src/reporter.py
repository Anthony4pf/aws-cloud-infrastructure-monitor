"""
reporter.py
-----------
Queries logged metrics from the database and outputs:
  - A terminal summary report
  - A CSV export for Excel / Tableau analysis
  - Optionally uploads the CSV to S3
"""

import csv
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import AWS_REGION, S3_BUCKET_NAME, DB_PATH
from src.logger import fetch_recent, fetch_summary, get_connection


def print_summary(instance_id):
    """Prints a human-readable performance summary to the terminal."""
    summary = fetch_summary(instance_id)
    print("\n" + "=" * 50)
    print(f"  Infrastructure Monitor — Summary Report")
    print(f"  Instance: {instance_id}")
    print("=" * 50)
    print(f"  Total readings     : {summary['total_readings']}")
    print(f"  Uptime             : {summary['uptime_pct']}%")
    print(f"  Average CPU        : {summary['avg_cpu']}%")
    print(f"  Peak CPU           : {summary['peak_cpu']}% (at {summary['peak_time']})")
    print(f"  Min CPU            : {summary['min_cpu']}%")
    print(f"  First reading      : {summary['first_reading']}")
    print(f"  Last reading       : {summary['last_reading']}")
    print("=" * 50 + "\n")


def export_csv(output_path="metrics_export.csv"):
    """Exports all metrics from the database to a CSV file."""
    with get_connection() as conn:
        conn.row_factory = __import__("sqlite3").Row
        cursor = conn.execute("SELECT * FROM metrics ORDER BY timestamp ASC")
        rows = cursor.fetchall()

    if not rows:
        print("[!] No data to export.")
        return None

    fieldnames = ["id", "timestamp", "instance_id",
                  "cpu_utilization", "network_in_bytes",
                  "network_out_bytes", "status"]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(dict(row))

    print(f"[+] CSV exported: {output_path} ({len(rows)} rows)")
    return output_path


def upload_to_s3(file_path):
    """Uploads a local file to the project S3 bucket."""
    import boto3
    s3 = boto3.client("s3", region_name=AWS_REGION)
    filename = os.path.basename(file_path)
    key = f"reports/{datetime.utcnow().strftime('%Y-%m-%d')}/{filename}"

    s3.upload_file(file_path, S3_BUCKET_NAME, key)
    print(f"[+] Uploaded to S3: s3://{S3_BUCKET_NAME}/{key}")


def check_alerts(instance_id, cpu_threshold=80.0):
    """
    Scans the database for readings that breached the CPU threshold.
    Prints a warning for each breach found.
    """
    with get_connection() as conn:
        conn.row_factory = __import__("sqlite3").Row
        cursor = conn.execute("""
            SELECT timestamp, cpu_utilization
            FROM metrics
            WHERE instance_id = ? AND cpu_utilization > ?
            ORDER BY timestamp DESC
        """, (instance_id, cpu_threshold))
        breaches = cursor.fetchall()

    if breaches:
        print(f"[!] CPU threshold ({cpu_threshold}%) breached {len(breaches)} time(s):")
        for b in breaches:
            print(f"    {b['timestamp']} — {b['cpu_utilization']}%")
    else:
        print(f"[✓] No CPU threshold breaches detected (threshold: {cpu_threshold}%)")


if __name__ == "__main__":
    if not os.path.exists(".instance_id"):
        print("[!] .instance_id not found. Run provisioner.py first.")
        sys.exit(1)

    with open(".instance_id") as f:
        instance_id = f.read().strip()

    print_summary(instance_id)
    check_alerts(instance_id)
    csv_path = export_csv()

    if csv_path:
        upload = input("\nUpload CSV to S3? (y/n): ").strip().lower()
        if upload == "y":
            upload_to_s3(csv_path)
