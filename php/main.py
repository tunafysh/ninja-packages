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
    run(" ".join(config_cmd), cwd=php_src)

    info("Compiling...")
    run(f"make -j{os.cpu_count()}", cwd=php_src)

    info("Installing...")
    run("make install", cwd=php_src)

    good(f"PHP installed at {paths['artifact']}")

# ---------------------------------------

# Windows Builder

# ---------------------------------------

def build_php_windows(paths, php_version, php_zip, php_url):
    info("Installing PHP builder powershell module...")
    run("powershell -Command ..\\windows_build.ps1", cwd=paths["build"])

    good(f"PHP installed at {paths['artifact']}")
    info(f"To use PHP, add {artifact_dir} to your PATH")
    info(f"You can customize php.ini at: {php_ini}")


# ---------------------------------------

# Main dispatcher

# ---------------------------------------

def main():
    php_version = "8.5.4"
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
        
    shutil.copy2(paths["root"] / "scaffold" / "*", paths["artifact"])

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
