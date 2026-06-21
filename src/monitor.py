"""
monitor.py
----------
Polls CloudWatch for EC2 metrics (CPU, network, status checks)
and passes them to the logger every POLL_INTERVAL_SECONDS.
"""

import boto3
import time
import sys
import os
from datetime import datetime, timezone, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import AWS_REGION, POLL_INTERVAL_SECONDS, METRIC_PERIOD_SECONDS
from src.logger import init_db, log_metric


def get_instance_id():
    """Reads the instance ID saved by provisioner.py."""
    if not os.path.exists(".instance_id"):
        raise FileNotFoundError(
            ".instance_id not found. Run provisioner.py first."
        )
    with open(".instance_id") as f:
        return f.read().strip()


def fetch_metric(cloudwatch, instance_id, metric_name, unit):
    """
    Fetches the most recent average value for a given CloudWatch metric.
    Returns None if no data is available yet (instance may need ~5 min to emit metrics).
    """
    now = datetime.now(timezone.utc)
    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName=metric_name,
        Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
        StartTime=now - timedelta(seconds=METRIC_PERIOD_SECONDS * 2),
        EndTime=now,
        Period=METRIC_PERIOD_SECONDS,
        Statistics=["Average"],
        Unit=unit
    )
    datapoints = response.get("Datapoints", [])
    if not datapoints:
        return None
    # Return most recent reading
    latest = sorted(datapoints, key=lambda x: x["Timestamp"])[-1]
    return round(latest["Average"], 4)


def fetch_instance_status(ec2_client, instance_id):
    """
    Checks EC2 instance health status checks.
    Returns 'ok', 'impaired', or 'insufficient-data'.
    """
    response = ec2_client.describe_instance_status(
        InstanceIds=[instance_id],
        IncludeAllInstances=True
    )
    statuses = response.get("InstanceStatuses", [])
    if not statuses:
        return "unknown"
    system_status = statuses[0]["SystemStatus"]["Status"]
    instance_status = statuses[0]["InstanceStatus"]["Status"]
    if system_status == "ok" and instance_status == "ok":
        return "ok"
    return f"system:{system_status} instance:{instance_status}"


def collect_metrics(cloudwatch, ec2_client, instance_id):
    """Collects all metrics for one poll cycle. Returns a dict."""
    timestamp = datetime.now(timezone.utc).isoformat()

    cpu = fetch_metric(cloudwatch, instance_id, "CPUUtilization", "Percent")
    net_in = fetch_metric(cloudwatch, instance_id, "NetworkIn", "Bytes")
    net_out = fetch_metric(cloudwatch, instance_id, "NetworkOut", "Bytes")
    status = fetch_instance_status(ec2_client, instance_id)

    metrics = {
        "timestamp": timestamp,
        "instance_id": instance_id,
        "cpu_utilization": cpu,
        "network_in_bytes": net_in,
        "network_out_bytes": net_out,
        "status": status
    }

    print(
        f"[{timestamp}] CPU: {cpu}% | "
        f"Net In: {net_in}B | Net Out: {net_out}B | "
        f"Status: {status}"
    )
    return metrics


def run_monitor(poll_once=False):
    """
    Main monitoring loop.
    Set poll_once=True for testing (runs a single cycle and exits).
    """
    instance_id = get_instance_id()
    cloudwatch = boto3.client("cloudwatch", region_name=AWS_REGION)
    ec2_client = boto3.client("ec2", region_name=AWS_REGION)

    init_db()
    print(f"[*] Monitoring instance: {instance_id}")
    print(f"[*] Poll interval: {POLL_INTERVAL_SECONDS}s | Press Ctrl+C to stop\n")

    try:
        while True:
            metrics = collect_metrics(cloudwatch, ec2_client, instance_id)
            log_metric(metrics)

            if poll_once:
                break
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("\n[*] Monitor stopped.")


if __name__ == "__main__":
    run_monitor()
