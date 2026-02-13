#!/usr/bin/env pwsh

# Get the primary IPv4 address
$ip = (Get-NetIPAddress -AddressFamily IPv4 `
        | Where-Object { $_.InterfaceAlias -notmatch "Loopback" -and $_.IPAddress -notmatch "^169\.254" } `
        | Select-Object -First 1 -ExpandProperty IPAddress)

if (-not $ip) {
    $ip = "127.0.0.1"
}

Write-Host "$ip`:8089"
