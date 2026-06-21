#!/bin/bash
# setup.sh — run once to prepare your development environment

set -e  # exit immediately on any error

echo "[*] Setting up Cloud Infrastructure Monitor..."

# Check Python version
python_version=$(python3 --version 2>&1)
echo "[+] Found: $python_version"

# Create and activate virtual environment
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "[+] Virtual environment activated"

# Install dependencies
echo "[*] Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "[+] Dependencies installed"

# Check AWS CLI
if command -v aws &> /dev/null; then
    echo "[+] AWS CLI found: $(aws --version)"
else
    echo "[!] AWS CLI not found. Install it from: https://aws.amazon.com/cli/"
    echo "    Then run: aws configure"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo "[+] Docker found: $(docker --version)"
else
    echo "[!] Docker not found. Install from: https://docs.docker.com/get-docker/"
fi

# Copy .env if it doesn't exist
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "[!] .env file created from .env.example — fill in your AWS credentials before running."
else
    echo "[~] .env already exists, skipping."
fi

echo ""
echo "[✓] Setup complete."
echo ""
echo "Next steps:"
echo "  1. Fill in your AWS credentials in .env"
echo "  2. Run: python main.py provision"
echo "  3. Run: python main.py monitor"
