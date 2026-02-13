#!/usr/bin/env pwsh

$ServiceName = "main_static"

# Check if service exists
$service = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue

if ($null -eq $service) {
    Write-Host "Service '$ServiceName' does not exist."
    exit 0
}

Write-Host "Stopping service..."
Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue

Write-Host "Deleting service..."
sc.exe delete $ServiceName | Out-Null

Start-Sleep -Seconds 1

Write-Host "Service deleted."
