#!/bin/bash

# Get the IP address of the primary network interface
IP=$(hostname -I | awk '{print $1}')

if [ -z "$IP" ]; then
  # Fallback to localhost
  IP="127.0.0.1"
fi

echo "$IP:8089"
