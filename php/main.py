import os
import platform
import subprocess
import sys
from pathlib import Path
from util import *

# ---------------------------------------

# Helpers

# ---------------------------------------

def project_paths():
    root = Path.cwd() / "php"
    return {"root": root, "build": root / "build", "artifact": root / "artifact"}

def prepare_dirs(paths):
    for p in paths.values():
        p.mkdir(parents=True, exist_ok=True)

def run_cmd(cmd, cwd=None):
    info(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

# ---------------------------------------

# Linux / macOS Builder

# ---------------------------------------

def build_php_unix(paths, php_version, php_tarball, php_url):
    info(f"Downloading PHP source: {php_url}")
    build_dir = paths["build"]
    download_file(php_url, str(build_dir / php_tarball))
    extract_tarball(str(build_dir / php_tarball), dest=str(build_dir))

    php_src = build_dir / f"php-{php_version}"

    config_cmd = [
        "./configure",
        f"--prefix={paths['artifact']}",
        "--enable-fpm",
        "--enable-so",
        "--enable-mbstring",
        "--with-mysqli",
        "--with-pdo-mysql",
        "--with-openssl",
        "--with-zlib",
    ]

    info("Configuring PHP...")
    run_cmd(" ".join(config_cmd), cwd=php_src)

    info("Compiling...")
    run_cmd(f"make -j{os.cpu_count()}", cwd=php_src)

    info("Installing...")
    run_cmd("make install", cwd=php_src)

    good(f"PHP installed at {paths['artifact']}")

# ---------------------------------------

# Windows Builder

# ---------------------------------------

def build_php_windows(paths, php_version, php_zip, php_url):
    """
    For Windows, we download the pre-built binaries from php.net
    Building PHP from source on Windows requires the PHP SDK which is complex.
    Using pre-built binaries is the recommended approach.
    """
    info(f"Downloading pre-built PHP for Windows: {php_url}")
    build_dir = paths["build"]
    artifact_dir = paths["artifact"]
    
    # PHP Windows binaries come as ZIP files
    # URL format: https://windows.php.net/downloads/releases/php-{version}-Win32-vs16-x64.zip
    # For newer versions, use: https://windows.php.net/downloads/releases/php-{version}-nts-Win32-vs16-x64.zip
    
    # Determine the correct Windows binary URL
    # Non-thread-safe (NTS) is recommended for most use cases
    windows_php_url = f"https://windows.php.net/downloads/releases/php-{php_version}-nts-Win32-vs16-x64.zip"
    windows_php_zip = f"php-{php_version}-nts-Win32-vs16-x64.zip"
    
    info(f"Attempting to download from: {windows_php_url}")
    
    try:
        download_file(windows_php_url, str(build_dir / windows_php_zip))
    except Exception as e:
        # Fallback to thread-safe version if NTS not available
        warn(f"NTS version not found, trying thread-safe version: {e}")
        windows_php_url = f"https://windows.php.net/downloads/releases/php-{php_version}-Win32-vs16-x64.zip"
        windows_php_zip = f"php-{php_version}-Win32-vs16-x64.zip"
        download_file(windows_php_url, str(build_dir / windows_php_zip))
    
    info(f"Extracting PHP to {artifact_dir}")
    extract_zip(str(build_dir / windows_php_zip), dest=str(artifact_dir))
    
    # Copy php.ini-production to php.ini if it doesn't exist
    php_ini_prod = artifact_dir / "php.ini-production"
    php_ini = artifact_dir / "php.ini"
    
    if php_ini_prod.exists() and not php_ini.exists():
        import shutil
        shutil.copy(php_ini_prod, php_ini)
        info("Created php.ini from php.ini-production")
    
    good(f"PHP installed at {paths['artifact']}")
    info(f"To use PHP, add {artifact_dir} to your PATH")
    info(f"You can customize php.ini at: {php_ini}")


# ---------------------------------------

# Main dispatcher

# ---------------------------------------

def main():
    php_version = "8.4.14"
    system = platform.system()

    paths = project_paths()
    prepare_dirs(paths)

    if system in ("Linux", "Darwin"):
        php_tarball = f"php-{php_version}.tar.gz"
        php_url = f"https://www.php.net/distributions/{php_tarball}"
        build_php_unix(paths, php_version, php_tarball, php_url)
    elif system == "Windows":
        php_zip = f"php-{php_version}.zip"
        php_url = f"https://www.php.net/distributions/{php_zip}"
        build_php_windows(paths, php_version, php_zip, php_url)
    else:
        raise RuntimeError(f"Unsupported OS: {system}")
        
    shutil.copy2("scaffold/.ninja", "artifact")

# ---------------------------------------

# Entry

# ---------------------------------------

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "clean":
        clean()
        sys.exit(0)

    try:
        main()
    except subprocess.CalledProcessError as e:
        err(f"Command failed: {e}")
        sys.exit(1)
    except Exception as e:
        err(str(e))
        sys.exit(1)
