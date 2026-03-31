@echo off
REM Build script for Windows (CMD)
REM Usage: build.bat

echo Building PHP...
uv run -m php.main
if %errorlevel% neq 0 (
    echo PHP build failed!
    exit /b %errorlevel%
)

echo Building Apache...
uv run -m apache.main
if %errorlevel% neq 0 (
    echo Apache build failed!
    exit /b %errorlevel%
)

echo Building MariaDB...
uv run -m mariadb.main
if %errorlevel% neq 0 (
    echo MariaDB build failed!
    exit /b %errorlevel%
)

echo All builds completed successfully!
