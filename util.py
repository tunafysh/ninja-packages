import hashlib
import os
import platform
import shutil
import sys
import subprocess
import tarfile
import urllib.request
import zipfile

from pathlib import Path
from tqdm import tqdm

# ----------------------------
# Colors
# ----------------------------
def c(text, color):
    if sys.stdout.isatty():
        return f"\033[{color}m{text}\033[0m"
    return text


def info(x): print(c(x, "36"))
def good(x): print(c(x, "32"))
def warn(x): print(c(x, "33"))
def err(x):  print(c(x, "31"))


# ----------------------------
# Helpers
# ----------------------------
def run(cmd, cwd=None, env=None):
    info(f"[RUN] {cmd} (cwd={cwd}) (env={env is not None})")
    subprocess.check_call(cmd, shell=True, cwd=cwd, env=env)

def _download(url, dest: Path):
    dest = Path(dest)  # ensure it's a Path object
    with urllib.request.urlopen(url) as response:
        total_size = int(response.getheader('Content-Length', 0))
        block_size = 8192
        with open(dest, 'wb') as f, tqdm(
            total=total_size, 
            unit='B', 
            unit_scale=True, 
            unit_divisor=1024, 
            desc=str(dest)  # <--- convert Path to string
        ) as bar:
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                f.write(buffer)
                bar.update(len(buffer))

def download_file(url, dest, checksum=None, retries=2):
    info(f"[DOWNLOAD] {url}")

    for attempt in range(1, retries + 1):
        _download(url, dest)

        if checksum is None:
            break

        info(f"[VERIFY] {dest}")
        if sha256_checksum(dest) == checksum:
            good(f"[SAVED] {dest}")
            return
        else:
            info(f"[CHECKSUM MISMATCH] Attempt {attempt}/{retries}")

    # If we reach here, all retries failed
    raise ValueError(f"Checksum verification failed for {dest} after {retries} attempts")


def extract_tarball(tarball_path, dest="."):
    info(f"[EXTRACT] {tarball_path} -> {dest}")
    with tarfile.open(tarball_path, "r:gz") as t:
        t.extractall(dest)
    good(f"[EXTRACTED] {tarball_path}")
    
def extract_zip(zip_path, dest="."):
    info(f"[EXTRACT] {zip_path} -> {dest}")
    with zipfile.ZipFile(zip_path, "r") as z:
        z.extractall(dest)
    good(f"[EXTRACTED] {zip_path}")
    
def clean():
    project_root = os.path.abspath(".")
    build_dir = os.path.join(project_root, "build")
    artifact_dir = os.path.join(project_root, "artifact")

    for d in (build_dir, artifact_dir):
        if os.path.exists(d):
            warn(f"Removing {d}")
            shutil.rmtree(d)
            good(f"Removed {d}")
        else:
            info(f"{d} does not exist, skipping")

def write_file(path, text):
    print(f"[WRITE] {os.path.basename(path)}")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)

def is_choco_package_installed(pkg_name):
    try:
        # Run `choco list --localonly --limit-output --exact <pkg>`
        result = subprocess.run(
            ["choco", "list", "--localonly", "--limit-output", "--exact", pkg_name],
            capture_output=True,
            text=True,
            check=False
        )
    except FileNotFoundError:
        # choco command not found
        return False
    
    output = result.stdout.strip()
    # If package is installed, choco outputs something like "pkg_name|version"
    if output:
        # Make sure it's the exact package entry
        # e.g. output == "git.install|2.39.0" or similar
        parts = output.split("|")
        if parts[0].lower() == pkg_name.lower():
            return True
    
    return False

def strip_extension(fn: str, extensions=[".tar.gz", ".tar.bz2"]):
    for ext in extensions:
        if fn.endswith(ext):
            return fn[:-len(ext)]
    return fn

def check_windows_tool(tool_name, install_hint=None):
    """Check if a Windows tool is available in PATH"""
    if shutil.which(tool_name):
        info(f"{tool_name} found: {shutil.which(tool_name)}")
        return True
    else:
        err(f"{tool_name} not found in PATH!")
        if install_hint:
            warn(f"Install hint: {install_hint}")
        return False

def verify_windows_build_env(required_tools):
    """Verify Windows build environment has required tools"""
    missing = []
    for tool, hint in required_tools.items():
        if not check_windows_tool(tool, hint):
            missing.append(tool)
    
    if missing:
        err(f"Missing required tools: {', '.join(missing)}")
        err("Please install the missing tools and ensure they are in your PATH.")
        return False
    
    good("All required build tools found!")
    return True

def tool_exists(tool_name):
    return shutil.which(tool_name) is not None

def install_go():
    if tool_exists("go"):
        info("Go is already installed.")
        return True
    
    
import os
from urllib.request import Request, urlopen

def download_go(system, arch, version="1.21.0", out_dir="."):
    ext = "zip" if system == "windows" else "tar.gz"

    filename = f"go{version}.{system}-{arch}.{ext}"
    filepath = os.path.join(out_dir, filename)
    url = f"https://go.dev/dl/{filename}"

    # Skip if already downloaded
    if os.path.exists(filepath):
        info(f"Using cached {filename}")
        return filepath

    info(f"⬇ Downloading {url}")

    req = Request(url, headers={
        "User-Agent": "Mozilla/5.0"  # avoids some weird blocking
    })

    try:
        with urlopen(req) as response, open(filepath, "wb") as out_file:
            total = response.length  # may be None
            downloaded = 0
            chunk_size = 8192

            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break
                out_file.write(chunk)
                downloaded += len(chunk)

                # Optional progress
                if total:
                    percent = downloaded * 100 // total
                    print(f"\r {percent}% ", end="")

        good("\nDownload complete")
        return filepath

    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        raise RuntimeError(f"Download failed: {e}")

def extract_go(filename, system):
    import os
import shutil
import tarfile
import zipfile
from pathlib import Path

def extract_go(archive_path, system, go_dir):
    info("Extracting Go...")

    archive_path = Path(archive_path)

    # Temporary extraction dir
    temp_dir = archive_path.parent / "_extract_tmp"

    if temp_dir.exists():
        shutil.rmtree(temp_dir)
    temp_dir.mkdir(parents=True)

    # Remove old Go install
    if go_dir.exists():
        shutil.rmtree(go_dir)

    # Extract into temp dir
    if archive_path.suffix == ".zip":
        with zipfile.ZipFile(archive_path, 'r') as z:
            z.extractall(temp_dir)
    else:
        with tarfile.open(archive_path, "r:gz") as t:
            t.extractall(temp_dir)

    # Move extracted "go" folder to your structure
    extracted_go = temp_dir / "go"

    if not extracted_go.exists():
        raise Exception("Go archive structure unexpected (missing 'go/' folder)")

    shutil.move(str(extracted_go), str(go_dir))

    # Cleanup
    shutil.rmtree(temp_dir)
    archive_path.unlink()

    good(f"Go installed at {go_dir}")

def get_system_arch():
    system = platform.system().lower()
    arch = platform.machine().lower()

    # Normalize OS names to match Go downloads
    if system.startswith("win"):
        system = "windows"
    elif system.startswith("darwin"):
        system = "darwin"
    elif system.startswith("linux"):
        system = "linux"
    else:
        raise Exception(f"Unsupported OS: {system}")

    # Normalize architecture
    if arch in ("x86_64", "amd64"):
        arch = "amd64"
    elif arch in ("aarch64", "arm64"):
        arch = "arm64"
    elif arch in ("i386", "i686"):
        arch = "386"
    else:
        raise Exception(f"Unsupported architecture: {arch}")

    return system, arch

def windows_dev_run(cmd, cwd=None, env=None):
    # On Windows, we want to run commands in a way that shows output in real-time
    # and also works well with PowerShell scripts.
    cmd = f"powershell -Command \"& 'C:\\Program Files\\Microsoft Visual Studio\\2022\\Community\\Common7\\Tools\\Launch-VsDevShell.ps1' && {cmd}\""
    info(f"[RUN] {cmd} (cwd={cwd}) (env={env is not None})")
    process = subprocess.Popen(cmd, shell=True, cwd=cwd, env=env)
    process.wait()
    if process.returncode != 0:
        raise subprocess.CalledProcessError(process.returncode, cmd)
    
def install_chocolatey():
    info("Installing Chocolatey...")
    cmd = 'powershell -Command "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString(\'https://chocolatey.org/install.ps1\'))"'
    subprocess.check_call(cmd, shell=True)
    good("Chocolatey installed successfully!")

def install_strawberryperl():
    if tool_exists("strawberryperl") or tool_exists("perl"):
        info("Strawberry Perl is already installed.")
        return True

    if not tool_exists("choco"):
        warn("Chocolatey not found. Installing Chocolatey first...")
        install_chocolatey()
    info("Installing Strawberry Perl via Chocolatey...")
    run("choco install strawberryperl -y")
    good("Strawberry Perl installed successfully!")

def install_bison():
    if not tool_exists("bison"):
        info("Bison not found. Installing WinFlexBison...")
        zip_url = "https://github.com/lexxmark/winflexbison/releases/download/v2.5.24/win_flex_bison-2.5.24.zip"
        zip_path = "winflexbison.zip"
        extract_path = "winflexbison"

        download_file(zip_url, zip_path)
        extract_zip(zip_path, extract_path)

        # Add bin to PATH
        os.environ["PATH"] += os.pathsep + os.path.abspath(os.path.join(extract_path, "bin"))
        info(f"WinFlexBison installed at {extract_path}/bin")

def sha256_checksum(file_path):
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()