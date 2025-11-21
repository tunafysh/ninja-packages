import shutil
import sys
import subprocess
import os
import tarfile
import urllib.request
import zipfile

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
def run(cmd, cwd=None):
    info(f"[RUN] {cmd} (cwd={cwd})")
    subprocess.check_call(cmd, shell=True, cwd=cwd)
    

def download_file(url, dest):
    info(f"[DOWNLOAD] {url}")
    with urllib.request.urlopen(url) as response:
        total_size = int(response.getheader('Content-Length', 0))
        block_size = 8192
        with open(dest, 'wb') as f, tqdm(total=total_size, unit='B', unit_scale=True, unit_divisor=1024, desc=dest) as bar:
            while True:
                buffer = response.read(block_size)
                if not buffer:
                    break
                f.write(buffer)
                bar.update(len(buffer))
    good(f"[SAVED] {dest}")


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