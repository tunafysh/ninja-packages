import os
import platform
import shutil
import subprocess
import re
import urllib.request
import sys

from util import *

PG_BASE_URL = "https://ftp.postgresql.org/pub/source/"


def get_latest_postgres():
    html = urllib.request.urlopen(PG_BASE_URL).read().decode()
    # find strings like v18.1/, v17.7/, etc.
    versions = re.findall(r"v(\d+(?:\.\d+){1,2})/", html)
    # normalize versions to 3‑component tuples for sorting
    def parse_ver(vstr):
        parts = vstr.split('.')
        # pad to length 3
        while len(parts) < 3:
            parts.append('0')
        return tuple(map(int, parts))
    versions_unique = sorted(set(versions), key=parse_ver)
    latest = versions_unique[-1]
    # use the exact version string as found for tarball name
    tarball = f"postgresql-{latest}.tar.gz"
    url = f"{PG_BASE_URL}v{latest}/{tarball}"
    return latest, tarball, url
    
def main():
    system = platform.system()
    project_root = os.path.abspath("./postgres")
    build_dir = os.path.join(project_root, "build")
    artifact_dir = os.path.join(project_root, "artifact", "postgres")

    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(artifact_dir, exist_ok=True)

    info(f"Working directory: {build_dir}")
    info(f"Artifact directory: {artifact_dir}")

    os.chdir(build_dir)

    # Clone PostgreSQL source
    pg_src_dir = os.path.join(build_dir, "postgres")
    pg_latest, pg_tarball, pg_url = get_latest_postgres()
    info(f"Latest PostgreSQL: {pg_latest} -> {pg_tarball}")
    download_file(pg_url, pg_tarball)
    extract_tarball(pg_tarball)
    shutil.move(strip_extension(pg_tarball), "postgres")

    # Linux / macOS Build
    if system in ("Linux", "Darwin"):
        info(f"Configuring PostgreSQL on {system}")

        os.environ["CFLAGS"] = "-O2 -Wall -std=gnu99 -pthread"

        configure_cmd = (
            f"./configure --prefix={artifact_dir} --with-openssl --with-readline "
        )

        run(configure_cmd, cwd=pg_src_dir)
        run(f"make -j{os.cpu_count()}", cwd=pg_src_dir)
        run("make install", cwd=pg_src_dir)

        good(f"PostgreSQL installed locally at {artifact_dir}")

    # Windows Build
    elif system == "Windows":
        # Ensure Perl
        perl_path = shutil.which("perl")
        if perl_path:
            info(f"Strawberry Perl already installed at: {perl_path}")
        else:
            info("Strawberry Perl not found. Installing...")
            run("winget install -e --id StrawberryPerl.StrawberryPerl")

        choco_path = shutil.which("choco")
        if choco_path:
            info(f"Chocolatey already installed at: {choco_path}")
        else:
            info("Chocolatey not found. Installing...")
            run("winget install Chocolatey")

        perl_path = is_choco_package_installed("winflexbison")
        if perl_path:
            info("Winflexbison already installed.")
        else:
            info("Winflexbison not found. Installing...")
            run("choco install winflexbison -y")

        if not shutil.which("python"):
            raise RuntimeError("Python is not installed")

        if not shutil.which("msbuild"):
            raise RuntimeError(
                "MSBuild not found – open 'x64 Native Tools Command Prompt for VS 2022'"
            )

        #
        # Create vcpkg manifest
        #
        vcpkg_json = os.path.join(build_dir, "postgres", "vcpkg.json")
        write_file(
            vcpkg_json,
            """
{
  "name": "postgres-build",
  "version": "1.0.0",

  "dependencies": [
    "openssl",
    "zlib"
  ]
}
""",
        )

        if not shutil.which("vcpkg"):
            raise RuntimeError("vcpkg is not installed or not found in PATH")

        # Install dependencies using manifest mode
        info("Installing dependencies via vcpkg manifest...")
        run(
            "vcpkg x-update-baseline --add-initial-baseline",
            cwd=os.path.join(build_dir, "postgres"),
        )
        run("vcpkg install", cwd=os.path.join(build_dir, "postgres"))

        inc_path = os.path.join(build_dir, "vcpkg_installed", "x64-windows", "include")
        lib_path = os.path.join(build_dir, "vcpkg_installed", "x64-windows", "lib")

        os.environ["INCLUDE"] = f"{inc_path};" + os.environ.get("INCLUDE", "")
        os.environ["LIB"] = f"{lib_path};" + os.environ.get("LIB", "")

        #
        # Build using official MSVC system
        #
        msvc_dir = os.path.join(pg_src_dir, "src", "tools", "msvc")

        info("Building PostgreSQL using src/tools/msvc/build...")

        # Build everything
        run("perl build.pl", cwd=msvc_dir)

        # Install to artifact folder
        run(f'perl build.pl install "{artifact_dir}"', cwd=msvc_dir)

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
        err(str(e))
        sys.exit(1)
