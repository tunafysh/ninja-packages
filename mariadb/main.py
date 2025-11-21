import os
import platform
import subprocess
import sys
from util import *

# ----------------------------
# Main
# ----------------------------
def main():
    system = platform.system()
    project_root = os.path.abspath(".").join("mariadb")
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
    cmake_cmd = (
        f"cmake .. "
        f"-DCMAKE_INSTALL_PREFIX={mariadb_artifact_dir} "
        f"-DWITH_SSL=system "
        f"-DWITH_ZLIB=system "
        f"-DWITH_UNIT_TESTS=OFF "
    )
    run(cmake_cmd, cwd=cmake_build_dir)

    info("Compiling MariaDB")
    run(f"cmake --build . -- -j{os.cpu_count()}", cwd=cmake_build_dir)

    info("Installing MariaDB locally")
    run("cmake --install .", cwd=cmake_build_dir)

    good(f"MariaDB installed locally at {mariadb_artifact_dir}")


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