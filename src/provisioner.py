"""
provisioner.py
--------------
Creates and manages AWS resources (EC2 instance, S3 bucket).
Run this on Day 1 to spin up your infrastructure.
"""

import boto3
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import (
    AWS_REGION, EC2_INSTANCE_TYPE, EC2_AMI_ID,
    EC2_KEY_NAME, EC2_SECURITY_GROUP, S3_BUCKET_NAME
)


def create_security_group(ec2_client):
    """Creates a security group that allows SSH access."""
    try:
        response = ec2_client.create_security_group(
            GroupName=EC2_SECURITY_GROUP,
            Description="Security group for cloud monitor project"
        )
        sg_id = response["GroupId"]

        # Allow SSH inbound (port 22)
        ec2_client.authorize_security_group_ingress(
            GroupId=sg_id,
            IpPermissions=[{
                "IpProtocol": "tcp",
                "FromPort": 22,
                "ToPort": 22,
                "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
            }]
        )
        print(f"[+] Security group created: {sg_id}")
        return sg_id

    except ec2_client.exceptions.ClientError as e:
        if "InvalidGroup.Duplicate" in str(e):
            # Already exists — retrieve its ID
            groups = ec2_client.describe_security_groups(
                GroupNames=[EC2_SECURITY_GROUP]
            )
            sg_id = groups["SecurityGroups"][0]["GroupId"]
            print(f"[~] Security group already exists: {sg_id}")
            return sg_id
        raise


def provision_ec2(ec2_resource, sg_id):
    """Launches a free-tier EC2 instance."""
    print("[*] Launching EC2 instance...")
    instances = ec2_resource.create_instances(
        ImageId=EC2_AMI_ID,
        InstanceType=EC2_INSTANCE_TYPE,
        MinCount=1,
        MaxCount=1,
        KeyName=EC2_KEY_NAME,
        SecurityGroupIds=[sg_id],
        TagSpecifications=[{
            "ResourceType": "instance",
            "Tags": [{"Key": "Name", "Value": "cloudmonitor-instance"}]
        }]
    )
    instance = instances[0]
    print(f"[*] Waiting for instance {instance.id} to enter running state...")
    instance.wait_until_running()
    instance.reload()
    print(f"[+] EC2 instance running: {instance.id} | Public IP: {instance.public_ip_address}")
    return instance.id


def provision_s3(s3_client):
    """Creates an S3 bucket for storing exported metric reports."""
    print(f"[*] Creating S3 bucket: {S3_BUCKET_NAME}")
    try:
        if AWS_REGION == "us-east-1":
            s3_client.create_bucket(Bucket=S3_BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=S3_BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": AWS_REGION}
            )
        print(f"[+] S3 bucket created: {S3_BUCKET_NAME}")
    except s3_client.exceptions.BucketAlreadyOwnedByYou:
        print(f"[~] S3 bucket already exists: {S3_BUCKET_NAME}")


def teardown_ec2(ec2_resource, instance_id):
    """Terminates an EC2 instance (use when done to avoid charges)."""
    print(f"[*] Terminating instance {instance_id}...")
    instance = ec2_resource.Instance(instance_id)
    instance.terminate()
    instance.wait_until_terminated()
    print(f"[+] Instance {instance_id} terminated.")


if __name__ == "__main__":
    ec2_client = boto3.client("ec2", region_name=AWS_REGION)
    ec2_resource = boto3.resource("ec2", region_name=AWS_REGION)
    s3_client = boto3.client("s3", region_name=AWS_REGION)

    sg_id = create_security_group(ec2_client)
    instance_id = provision_ec2(ec2_resource, sg_id)
    provision_s3(s3_client)

    # Save instance ID to a local file so other scripts can read it
    with open(".instance_id", "w") as f:
        f.write(instance_id)

    print(f"\n[✓] Infrastructure provisioned successfully.")
    print(f"    Instance ID saved to .instance_id")
    print(f"    Run monitor.py next to start collecting metrics.")
