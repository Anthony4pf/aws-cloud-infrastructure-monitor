import os
from dotenv import load_dotenv

load_dotenv()

# AWS
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

# EC2
EC2_INSTANCE_TYPE = "t3.micro"
EC2_AMI_ID = "ami-0c02fb55956c7d316"   # Amazon Linux 2 (us-east-1) — update per region
EC2_KEY_NAME = os.getenv("EC2_KEY_NAME", "cloudmonitor-key")
EC2_SECURITY_GROUP = "cloudmonitor-sg"

# S3
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "cloudmonitor-metrics-bucket")

# Monitoring
POLL_INTERVAL_SECONDS = 60      # how often to collect metrics
METRIC_PERIOD_SECONDS = 300     # CloudWatch aggregation window (5 min minimum)

# Database
DB_PATH = os.getenv("DB_PATH", "metrics.db")
