#!/bin/bash

SERVICE_NAME="main_static"

sudo systemctl restart $SERVICE_NAME
echo "Service restarted."
