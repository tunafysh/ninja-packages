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
    Build-Component -Name "PHP" -Module "php.main"
    Build-Component -Name "Apache" -Module "apache.main"
    Build-Component -Name "MariaDB" -Module "mariadb.main"
    
    Write-Host "`nAll builds completed successfully!" -ForegroundColor Green
}
catch {
    Write-Host "`nBuild process failed!" -ForegroundColor Red
    exit 1
}
