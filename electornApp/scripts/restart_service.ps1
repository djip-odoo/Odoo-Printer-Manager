#!/usr/bin/env pwsh
# Simple Windows service restart script

$serviceName = "main_static"

Write-Host "🔄 Restarting $serviceName ..."

# Stop service (ignore errors if already stopped)
Stop-Service -Name $serviceName -ErrorAction SilentlyContinue

Start-Sleep -Seconds 1

# Start service again
Start-Service -Name $serviceName -ErrorAction SilentlyContinue

# Check status
$status = (Get-Service -Name $serviceName).Status

if ($status -eq "Running") {
    Write-Host "✅ Service restarted successfully."
} else {
    Write-Host "❌ Failed to restart service. Current status: $status"
}
