#!/bin/bash

set -e

echo "📦 Creating virtual environment..."

python3 -m venv venv
source ./venv/bin/activate

echo "📥 Installing requirements..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install nuitka

echo "🔍 Locating escpos capabilities.json..."
CAP_JSON=$(find ./venv -name capabilities.json | head -n 1)

echo "🛠️ Building executable with PyInstaller..."
nuitka \
  --standalone \
  --onefile \
  --include-data-file="ssl/printer-server.local.crt=ssl/printer-server.local.crt" \
  --include-data-file="ssl/printer-server.local.key=ssl/printer-server.local.key" \
  --assume-yes-for-downloads \
  --include-data-file=templates/index.html=templates/index.html \
  --include-data-file="$CAP_JSON"=escpos/$(basename "$CAP_JSON") \
  main.py

echo "✅ Nuitka build complete. Binary is inside: ./main.dist/"
