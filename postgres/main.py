import os
import platform
import re
import sys
import shutil
import urllib.request
from util import *

PG_BASE_URL = "https://ftp.postgresql.org/pub/source/"

def get_latest_postgres():
    html = urllib.request.urlopen(PG_BASE_URL).read().decode()
    versions = re.findall(r"v(\d+\.\d+\.\d+)/", html)
    latest = sorted(versions, key=lambda v: tuple(map(int, v.split("."))))[-1]
    tarball = f"postgresql-{latest}.tar.gz"
    url = f"{PG_BASE_URL}v{latest}/{tarball}"
    return latest, tarball, url


def main():
    system = platform.system()
    project_root = os.path.abspath(".")
    build_dir = os.path.join(project_root, "build")
    artifact_dir = os.path.join(project_root, "artifact")

    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(artifact_dir, exist_ok=True)
    info(f"Working directory: {build_dir}")
    info(f"Artifact directory: {artifact_dir}")

    os.chdir(build_dir)

    pg_latest, pg_tarball, pg_url = get_latest_postgres()
    info(f"Latest PostgreSQL: {pg_latest} -> {pg_tarball}")
    download_file(pg_url, pg_tarball)
    extract_tarball(pg_tarball)

    pg_src_dir = os.path.join(build_dir, f"postgresql-{pg_latest}")

    if system in ("Linux", "Darwin"):
        info(f"Configuring PostgreSQL on {system}")

        os.environ["CFLAGS"] = "-O2 -Wall -std=gnu99 -pthread"

        configure_cmd = (
            f'./configure '
            f'--prefix={artifact_dir} '
            f'--with-openssl '
            f'--with-readline '
            f''
        )

        run(configure_cmd, cwd=pg_src_dir)
        run(f"make -j{os.cpu_count()}", cwd=pg_src_dir)
        run("make install", cwd=pg_src_dir)
        good(f"PostgreSQL installed locally at {artifact_dir}")


    elif system == "Windows":
        info(f"Configuring PostgreSQL for Windows in {artifact_dir}")
        msvc_build_dir = os.path.join(build_dir, "msvc_build")
        os.makedirs(msvc_build_dir, exist_ok=True)
        run(f'cmake ..\\postgresql-{pg_latest} -G "Visual Studio 17 2022" -DCMAKE_INSTALL_PREFIX={artifact_dir}', cwd=msvc_build_dir)
        run("cmake --build . --config Release --target INSTALL", cwd=msvc_build_dir)
        good(f"PostgreSQL installed locally at {artifact_dir}")

    else:
        raise RuntimeError(f"Unsupported OS: {system}")


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
