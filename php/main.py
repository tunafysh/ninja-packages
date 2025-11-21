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
# Linux + macOS Builder
# ---------------------------------------
def build_php_unix(system, paths, php_version, php_tarball, php_url):
    info(f"Downloading PHP source: {php_url}")
    os.chdir(paths["build"])

    download_file(php_url, php_tarball)
    extract_tarball(php_tarball)

    php_src = paths["build"] / f"php-{php_version}"

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
    run(" ".join(config_cmd), cwd=str(php_src))

    info("Compiling...")
    run(f"make -j{os.cpu_count()}", cwd=str(php_src))

    info("Installing...")
    run("make install", cwd=str(php_src))

    good(f"PHP installed at {paths['artifact']}")


# ---------------------------------------
# Windows Builder
# ---------------------------------------
def build_php_windows(paths, php_version, php_zip, php_url):
    info("Preparing Windows PHP build")

    # Windows uses ZIP instead of tar.gz
    os.chdir(paths["build"])

    download_file(php_url, php_zip)
    extract_zip(php_zip)

    php_src = paths["build"] / f"php-{php_version}"

    # Windows needs PHP SDK + configure.js
    configure_js = php_src / "configure.js"
    if not configure_js.exists():
        raise RuntimeError("configure.js not found. Use official PHP SDK!")

    info("Running Windows PHP configure.js")

    run(
        f"cscript //nologo configure.js "
        f'--prefix="{paths["artifact"]}" '
        f"--enable-snapshot-build ",
        cwd=str(php_src),
    )

    info("Compiling (nmake)...")
    run("nmake", cwd=str(php_src))
    run("nmake install", cwd=str(php_src))

    good(f"PHP installed at {paths['artifact']}")


# ---------------------------------------
# Main dispatcher
# ---------------------------------------
def main():
    php_version = "8.4.14"
    php_tarball = f"php-{php_version}.tar.gz"
    php_zip = f"php-{php_version}.zip"
    php_url = f"https://www.php.net/distributions/{php_tarball}"

    system = platform.system()
    paths = project_paths()

    prepare_dirs(paths)
    info(f"Platform: {system}")
    info(f"PHP version: {php_version}")
    info(f"Artifact directory: {paths['artifact']}")

    if system in ("Linux", "Darwin"):
        build_php_unix(system, paths, php_version, php_tarball, php_url)
    elif system == "Windows":
        build_php_windows(paths, php_version, php_zip, php_url)
    else:
        raise RuntimeError(f"Unsupported OS: {system}")


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
        err(f"{e}")
        sys.exit(1)
