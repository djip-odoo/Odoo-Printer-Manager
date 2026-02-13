#!/bin/bash
# Usage: ./add_service.sh /path/to/main.bin

SERVICE_NAME="main_static"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
MAIN_BIN="$1"

# Ensure binary is executable
sudo chmod +x "$MAIN_BIN"

# Write systemd service
echo "[Unit]
Description=Main Static Service
After=network.target

[Service]
ExecStart=$MAIN_BIN
WorkingDirectory=$(dirname "$MAIN_BIN")
Restart=always
User=root
StandardOutput=journal
StandardError=journal
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target" | sudo tee "$SERVICE_FILE" > /dev/null

# Reload systemd & start service
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

IP=$(hostname -I | awk '{print $1}')
if [ -z "$IP" ]; then IP="127.0.0.1"; fi

echo "Service created & started. Current device IP address: $IP:8089"
