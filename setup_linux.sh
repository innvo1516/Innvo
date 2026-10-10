#!/usr/bin/env bash
# ==========================================================
# Innvo - 1-Click Setup Script for Linux / Raspberry Pi
# ==========================================================

echo "⚡ [Innvo] Installing dependencies on Linux / Raspberry Pi..."

sudo apt update -y
sudo apt install -y python3 python3-pip python3-venv git libasound2-dev

# Virtual Environment
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# Sign constitution for security verification
python3 security/admin_cli.py sign-rules

echo "=========================================================="
echo "✅ [Innvo] Setup Complete on Linux / Raspberry Pi!"
echo "To start Innvo, run: python3 main.py"
echo "=========================================================="
