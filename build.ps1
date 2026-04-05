#!/usr/bin/env pwsh
# Build script for Windows (PowerShell)
# Usage: .\build.ps1

$ErrorActionPreference = "Stop"

function Build-Component {
    param(
        [string]$Name,
        [string]$Module
    )
    
    Write-Host "Building $Name..." -ForegroundColor Cyan
    
    try {
        uv run -m $Module
        Write-Host "$Name build completed successfully!" -ForegroundColor Green
    }
    catch {
        Write-Host "$Name build failed!" -ForegroundColor Red
        throw
    }
}

try {
    Write-Host "`n Starting Bulk builds.`n" -ForegroundColor Cyan
    Build-Component -Name "PHP" -Module "php.main"
    Build-Component -Name "Caddy" -Module "caddy.main"
    Build-Component -Name "MariaDB" -Module "mariadb.main"
    Build-Component -Name "Postgres" -Module "postgres.main"
    
    Write-Host "`nAll builds completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "`nBuild process failed!" -ForegroundColor Red
    exit 1
}
