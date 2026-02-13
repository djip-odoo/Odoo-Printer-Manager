#!/usr/bin/env pwsh
# Abort on any failure
$ErrorActionPreference = "Stop"

$serviceName = "main_static"

# Accept external executable path
if ($args.Count -gt 0) {
    $mainBin = $args[0]
} else {
    $scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
    $mainBin = Join-Path $scriptDir "main.exe"
}

Write-Host "Using main executable: $mainBin"

if (-Not (Test-Path $mainBin)) {
    throw "Executable not found: $mainBin"
}

# Remove service if exists
if (Get-Service -Name $serviceName -ErrorAction SilentlyContinue) {
    Write-Host "Removing existing service..."
    sc.exe stop $serviceName | Out-Null
    sc.exe delete $serviceName | Out-Null
    Start-Sleep -Seconds 2
}

Write-Host "Creating Windows service..."

# RUN sc.exe CREATE AND CAPTURE ERRORS
$create = sc.exe create $serviceName binPath= "\"$mainBin\"" start= auto

if ($create -notmatch "SUCCESS") {
    throw "Failed to create service. sc.exe output:`n$create"
}

# Verify service exists before editing registry
if (-Not (Test-Path "HKLM:\SYSTEM\CurrentControlSet\Services\$serviceName")) {
    throw "Service registry path missing. Service creation failed."
}

# Set working directory
$workDir = Split-Path -Parent $mainBin

Set-ItemProperty `
  -Path "HKLM:\SYSTEM\CurrentControlSet\Services\$serviceName" `
  -Name "ImagePath" `
  -Value "\"$mainBin\" --workdir \"$workDir\""

Write-Host "Starting service..."
$start = sc.exe start $serviceName
if ($start -notmatch "SUCCESS") {
    throw "Failed to start service. sc.exe output:`n$start"
}

# Get IP
$ip = (Get-NetIPAddress -AddressFamily IPv4 |
        Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -notmatch '^169\.254' } |
        Select-Object -First 1 -ExpandProperty IPAddress)

if (-Not $ip) { $ip = "127.0.0.1" }

Write-Host "Service created and started successfully."
Write-Host ("Current device IP: http://{0}:8089" -f $ip)
