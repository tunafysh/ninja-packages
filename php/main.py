import os
import platform
import subprocess
import urllib.request
import tarfile
import sys
from tqdm import tqdm
import shutil

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
def err(x): print(c(x, "31"))

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


# ----------------------------
# CLEAN
# ----------------------------
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


# ----------------------------
# Main
# ----------------------------
def main():
    system = platform.system()
    project_root = os.path.abspath(".")
    build_dir = os.path.join(project_root, "build")
    php_artifact_dir = os.path.join(project_root, "artifact")

    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(php_artifact_dir, exist_ok=True)
    info(f"Working directory: {build_dir}")
    info(f"PHP artifact directory: {php_artifact_dir}")

    os.chdir(build_dir)

    php_version = "8.4.14"
    php_tarball = "php-8.4.14.tar.gz"
    php_url     = "https://www.php.net/distributions/php-8.4.14.tar.gz"

    info(f"PHP version: {php_version}")

    download_file(php_url, php_tarball)
    extract_tarball(php_tarball)

    php_src_dir = os.path.join(build_dir, f"php-{php_version}")

    apxs_path = os.path.abspath(os.path.join(project_root, "..", "apache", "artifact", "bin", "apxs"))
    info(f"Using APXS: {apxs_path}")

    if system in ("Linux", "Darwin"):
        info(f"Configuring PHP on {system}")

        config_cmd = (
            f"./configure "
            f"--prefix={php_artifact_dir} "
            "--enable-fpm "
            "--enable-so "
            "--enable-mbstring "
            "--with-mysqli "
            "--with-pdo-mysql "
            "--with-openssl "
            "--with-zlib"
        )

        info(f"PHP will be compiled with configuration: {config_cmd}")

        run(config_cmd, cwd=php_src_dir)
        run(f"make -j{os.cpu_count()}", cwd=php_src_dir)
        run("make install", cwd=php_src_dir)
        good(f"PHP installed locally at {php_artifact_dir}")

    else:
        raise RuntimeError("windows PHP build not implemented yet")


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
