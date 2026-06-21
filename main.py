"""
main.py
-------
Entry point for the AWS Cloud Infrastructure Monitor.

Usage:
    python main.py provision    # Day 1: create EC2 + S3
    python main.py monitor      # Day 2-3: start metric collection loop
    python main.py report       # Day 4: print summary + export CSV
    python main.py teardown     # Terminate EC2 instance (avoids charges)
"""

import sys
import os


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "provision":
        from src.provisioner import (
            create_security_group, provision_ec2, provision_s3
        )
        import boto3
        from config.config import AWS_REGION

        ec2_client = boto3.client("ec2", region_name=AWS_REGION)
        ec2_resource = boto3.resource("ec2", region_name=AWS_REGION)
        s3_client = boto3.client("s3", region_name=AWS_REGION)

        sg_id = create_security_group(ec2_client)
        instance_id = provision_ec2(ec2_resource, sg_id)
        provision_s3(s3_client)

        with open(".instance_id", "w") as f:
            f.write(instance_id)
        print(f"\n[✓] Done. Instance ID: {instance_id}")

    elif command == "monitor":
        from src.monitor import run_monitor
        run_monitor()

    elif command == "report":
        from src.reporter import print_summary, check_alerts, export_csv
        if not os.path.exists(".instance_id"):
            print("[!] No instance found. Run: python main.py provision")
            sys.exit(1)
        with open(".instance_id") as f:
            instance_id = f.read().strip()
        print_summary(instance_id)
        check_alerts(instance_id)
        export_csv()

    elif command == "teardown":
        from src.provisioner import teardown_ec2
        import boto3
        from config.config import AWS_REGION
        if not os.path.exists(".instance_id"):
            print("[!] No instance ID found.")
            sys.exit(1)
        with open(".instance_id") as f:
            instance_id = f.read().strip()
        ec2_resource = boto3.resource("ec2", region_name=AWS_REGION)
        teardown_ec2(ec2_resource, instance_id)
        os.remove(".instance_id")

    else:
        print(f"[!] Unknown command: {command}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
