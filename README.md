# ninja-packages
A collection of python scripts, packages and configs to serve as a jumpstart for Ninja, the tech stack management platform.

## Building

This project includes build scripts for PHP, Apache, and MariaDB that work cross-platform.

### Linux / macOS

```bash
./build.sh
```

Or build individual components:
```bash
uv run -m php.main
uv run -m apache.main
uv run -m mariadb.main
uv run -m postgres.main
```

### Windows

**Using Command Prompt (CMD):**
```cmd
build.bat
```

**Using PowerShell:**
```powershell
.\build.ps1
```

Or build individual components:
```cmd
uv run -m php.main
uv run -m apache.main
uv run -m mariadb.main
uv run -m postgres.main
```

### Clean Build Artifacts

To clean build and artifact directories:

**Linux/macOS:**
```bash
uv run -m php.main clean
uv run -m apache.main clean
uv run -m mariadb.main clean
uv run -m postgres.main clean
```