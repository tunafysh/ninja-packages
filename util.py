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
