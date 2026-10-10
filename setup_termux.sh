#!/data/data/com.termux/files/usr/bin/bash
# ==========================================================
# Innvo - 1-Click Setup Script for Android (Termux)
# ==========================================================

echo "⚡ [Innvo] Installing dependencies on Android Termux..."

pkg update -y && pkg upgrade -y
pkg install -y python git clang termux-api pulseaudio

# Install Python requirements
pip install --upgrade pip
pip install -r requirements.txt

# Sign constitution for security verification
python security/admin_cli.py sign-rules

echo "=========================================================="
echo "✅ [Innvo] Setup Complete on Android Termux!"
echo "To start Innvo, run: python main.py"
echo "=========================================================="
