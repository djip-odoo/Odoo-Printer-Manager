#!/bin/bash

SERVICE_NAME="main_static"

sudo systemctl stop $SERVICE_NAME
sudo systemctl disable $SERVICE_NAME
sudo rm -f /etc/systemd/system/$SERVICE_NAME.service
sudo systemctl daemon-reload

echo "Service deleted."
