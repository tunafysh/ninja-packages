import os
import platform
import subprocess
import sys
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
def err(x):  print(c(x, "31"))


# ----------------------------
# Helpers
# ----------------------------
def run(cmd, cwd=None):
    info(f"[RUN] {cmd} (cwd={cwd})")
    subprocess.check_call(cmd, shell=True, cwd=cwd)


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