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
    
    # Windows-specific configuration
    if system == "Windows":
        info("Configuring for Windows with Visual Studio")
        cmake_args.extend([
            '-G "Visual Studio 17 2022"',
            '-A x64',
            '-DCMAKE_BUILD_TYPE=Release'
        ])
        
        # Check for required tools on Windows
        required_tools = {
            "cmake": "Install CMake from https://cmake.org/download/",
            "msbuild": "Install Visual Studio 2022 (Community Edition is free)",
        }
        if not verify_windows_build_env(required_tools):
            raise RuntimeError("Missing required build tools for Windows")
    
    run(" ".join(cmake_args), cwd=cmake_build_dir)

    info("Compiling MariaDB")
    if system == "Windows":
        run("cmake --build . --config Release", cwd=cmake_build_dir)
    else:
        run(f"cmake --build . -- -j{os.cpu_count()}", cwd=cmake_build_dir)

    info("Installing MariaDB locally")
    if system == "Windows":
        run("cmake --install . --config Release", cwd=cmake_build_dir)
    else:
        run("cmake --install .", cwd=cmake_build_dir)

    good(f"MariaDB installed locally at {mariadb_artifact_dir}")
    shutil.copy2("scaffold/.ninja", "artifact")


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