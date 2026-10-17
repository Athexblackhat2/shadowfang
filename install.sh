#!/bin/bash
# ShadowFang - Requirements Installer

echo "[+] Installing ShadowFang requirements..."

pip install --upgrade pip
pip install -r requirements.txt

echo "[✓] All requirements installed!"
echo "[*] Run: python builder.py"