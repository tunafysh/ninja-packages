from util import *
from pathlib import Path
import os
import shutil

BASE_DIR = Path.cwd() / "caddy"
BUILD_DIR = BASE_DIR / "build"
ARTIFACT_DIR = BASE_DIR / "artifact"
GO_DIR = BUILD_DIR / "go"
GO_VERSION = "1.21.0"

def go_bin_path(system):
    return GO_DIR / "bin" / ("go.exe" if system == "windows" else "go")

def xcaddy_path():
    return BUILD_DIR / ("xcaddy.exe" if os.name == "nt" else "xcaddy")

def caddy_path():
    return ARTIFACT_DIR / ("caddy.exe" if os.name == "nt" else "caddy")

def main():
    system, arch = get_system_arch()

    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    os.makedirs(ARTIFACT_DIR, exist_ok=True)

    go_bin = go_bin_path(system)

    # Install Go locally
    if not go_bin.exists():
        info("Installing Go locally...")
        filename = download_go(system, arch)
        extract_go(filename, system, GO_DIR)
        good(f"Go downloaded and extracted to {GO_DIR}")
    else:
        good("Go already installed locally.")

    # Verify Go
    run(f"{str(go_bin)} version")

    # Install xcaddy
    xcaddy_bin = xcaddy_path()

    if not xcaddy_bin.exists():
        info("Installing xcaddy...")
        env = os.environ.copy()
        env["GOBIN"] = str(BUILD_DIR)

        run(f"{str(go_bin)} install github.com/caddyserver/xcaddy/cmd/xcaddy@latest", env=env)
    else:
        good("xcaddy already installed.")

    # Build Caddy
    caddy_bin = caddy_path()

    plugins = [
#        "github.com/caddyserver/transform-templates",
    ]

    if not caddy_bin.exists():
        info("Building Caddy...")
        run(f"{str(xcaddy_bin)} build {"--with" + ','.join(plugins) if len(plugins) > 0 else ''}--output {str(caddy_bin)}")
    else:
        good("Caddy already built.")

    good("\n Done!")
    good(f"Go: {go_bin}")
    good(f"xcaddy: {xcaddy_bin}")
    good(f"Caddy: {caddy_bin}")

if __name__ == "__main__":
    main()