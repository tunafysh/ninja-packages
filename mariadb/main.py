# starting over using the mariadb rest api to get prebuilts for linux and windows.

import platform
import requests
import json
import toml
if platform.system() == "Windows":
    import zipfile
elif platform.system() == "Linux":
    import tarfile

from util import *
from pathlib import Path

def get_paths():
    root = Path.cwd() / "mariadb"
    return { "root": root, "artifact": root / "artifact", "build": root / "build"}

def get_major_release(url):
    res = requests.get(url)
    data = res.json()
    releases = data["major_releases"]
    latest = next((r for r in releases if r["release_status"] == "Stable"), None)
    return latest["release_id"]

def update_shuriken_version(root, version):
    manifest_path = root / "scaffold" / "manifest.toml"
    with open(manifest_path, "r") as t:
        data = toml.load(t)

    if "shuriken" not in data:
        data["shuriken"] = {}
    data["shuriken"]["version"] = version

        
    with open(manifest_path, "w") as f:
        toml.dump(data, f)
    
def fetch_artifact(url, version, artifact_path):
    res = requests.get(f"{url}{version}/")
    data = res.json()
    releases = data["releases"]
    version, info = next(iter(releases.items()))
    files = info["files"]

    if platform.system() == "Windows":
        os_id = "Windows"
        preferred_package_type = "ZIP file"
    elif platform.system() == "Linux":
        os_id = "Linux"
        preferred_package_type = "gzipped tar file"
    else:
        os_id = "Source"
        preferred_package_type = None

    artifact = next((r for r in files if r["package_type"] == preferred_package_type and
     r["os"] == os_id and
     r["cpu"] == platform.machine()), None)
    
    download_url = artifact["file_download_url"]
    checksum = artifact["checksum"]["sha256sum"]
    return (version, download_url, checksum)

def download_win_linux():
    url = "https://downloads.mariadb.org/rest-api/mariadb/"
    paths = get_paths()

    if not paths["build"].exists(): paths["build"].mkdir(parents=True, exist_ok=True)
    if not paths["artifact"].exists(): paths["artifact"].mkdir(parents=True, exist_ok=True)

    info("Fetching MariaDB through REST API")
    
    major_release = get_major_release(url)
    version, archive_url, checksum = fetch_artifact(url, major_release, paths["artifact"])

    archive_path = paths["build"] / "latest.tar.gz" if platform.system() == "Linux" else paths["build"] / "latest.zip"

    download_file(archive_url, archive_path, checksum=checksum)

    if platform.system() == "Windows":
        extract_zip(archive_path, paths["build"])
    elif platform.system() == "Linux":
        extract_tarball(archive_path, paths["build"])
    update_shuriken_version(paths["root"], version)
    
def mac_main():
    project_root = os.path.join(os.path.abspath("."), "mariadb")
    build_dir = os.path.join(project_root, "build")
    mariadb_artifact_dir = os.path.join(project_root, "artifact")
    mariadb_repo_url = "https://github.com/MariaDB/server.git"
    mariadb_src_dir = os.path.join(build_dir, "mariadb-server")

    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(mariadb_artifact_dir, exist_ok=True)
    info(f"Working directory: {build_dir}")
    info(f"MariaDB artifact directory: {mariadb_artifact_dir}")

    if not os.path.exists(mariadb_src_dir):
        info("Cloning MariaDB repository")
        run(f"git clone {mariadb_repo_url} {mariadb_src_dir}")
    else:
        info("MariaDB source already exists, pulling latest changes")
        run("git pull", cwd=mariadb_src_dir)

    info("Initializing submodules")
    run("git submodule update --init --recursive", cwd=mariadb_src_dir)

    cmake_build_dir = os.path.join(mariadb_src_dir, "build")
    os.makedirs(cmake_build_dir, exist_ok=True)

    info("Configuring MariaDB with CMake")
    
    # Base CMake configuration
    cmake_args = [
        "cmake ..",
        f"-DCMAKE_INSTALL_PREFIX={mariadb_artifact_dir}",
        "-DWITH_SSL=system",
        "-DWITH_ZLIB=system",
        "-DWITH_UNIT_TESTS=OFF",
    ]
    
    run(" ".join(cmake_args), cwd=cmake_build_dir)

    info("Compiling MariaDB")
    run(f"cmake --build . -- -j{os.cpu_count()}", cwd=cmake_build_dir)

    info("Installing MariaDB locally")
    run("cmake --install .", cwd=cmake_build_dir)

    good(f"MariaDB installed locally at {mariadb_artifact_dir}")

def main():
    if platform.system() in ["Windows", "Linux"]:
        download_win_linux()
    elif platform.system() == "Darwin":
        mac_main()
    else:
        error(f"Unsupported platform: {platform.system()}")
    
    shutil.copy2("scaffold/*", "artifact/")

if __name__ == "__main__":
    main()
