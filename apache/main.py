import os
import platform
import re
import subprocess
import sys
import shutil
from util import *

def get_latest_apache():
    index_url = "https://downloads.apache.org/httpd/"
    html = urllib.request.urlopen(index_url).read().decode()
    versions = re.findall(r"httpd-(\d+\.\d+\.\d+)\.tar\.gz", html)
    latest = sorted(versions, key=lambda v: tuple(map(int, v.split("."))))[-1]
    tarball = f"httpd-{latest}.tar.gz"
    url = index_url + tarball
    return latest, tarball, url


def get_latest_apr():
    apr_index = "https://downloads.apache.org/apr/"

    html_apr = urllib.request.urlopen(apr_index).read().decode()
    apr_versions = re.findall(r"apr-(\d+\.\d+\.\d+)\.tar\.gz", html_apr)
    latest_apr = sorted(apr_versions, key=lambda v: tuple(map(int, v.split("."))))[-1]
    apr_tarball = f"apr-{latest_apr}.tar.gz"
    apr_url = apr_index + apr_tarball

    util_versions = re.findall(r"apr-util-(\d+\.\d+\.\d+)\.tar\.gz", html_apr)
    latest_util = sorted(util_versions, key=lambda v: tuple(map(int, v.split("."))))[-1]
    util_tarball = f"apr-util-{latest_util}.tar.gz"
    util_url = apr_index + util_tarball

    return (latest_apr, apr_tarball, apr_url), (latest_util, util_tarball, util_url)

# ----------------------------
# Main
# ----------------------------
def main():
    system = platform.system()
    project_root = os.path.abspath(".").join("apache")
    build_dir = os.path.join(project_root, "build")
    artifact_dir = os.path.join(project_root, "artifact")

    os.makedirs(build_dir, exist_ok=True)
    os.makedirs(artifact_dir, exist_ok=True)
    info(f"Working directory: {build_dir}")
    info(f"Artifact directory: {artifact_dir}")

    os.chdir(build_dir)

    apache_latest, apache_tarball, apache_url = get_latest_apache()
    info(f"Latest Apache: {apache_latest} -> {apache_tarball}")
    download_file(apache_url, apache_tarball)
    extract_tarball(apache_tarball)

    apache_src_dir = os.path.join(build_dir, f"httpd-{apache_latest}")

    (apr_latest, apr_tarball, apr_url), (util_latest, util_tarball, util_url) = get_latest_apr()
    info(f"Latest APR: {apr_latest} -> {apr_tarball}")
    info(f"Latest APR-util: {util_latest} -> {util_tarball}")

    download_file(apr_url, apr_tarball)
    download_file(util_url, util_tarball)

    extract_tarball(apr_tarball)
    extract_tarball(util_tarball)

    srclib_dir = os.path.join(apache_src_dir, "srclib")
    os.makedirs(srclib_dir, exist_ok=True)
    shutil.move(os.path.join(build_dir, f"apr-{apr_latest}"), os.path.join(srclib_dir, "apr"))
    shutil.move(os.path.join(build_dir, f"apr-util-{util_latest}"), os.path.join(srclib_dir, "apr-util"))
    info(f"APR + APR-util moved into {srclib_dir}")

    if system in ("Linux", "Darwin"):
        info(f"Configuring Apache on {system}")
        run(f"./configure --prefix={artifact_dir} --enable-so --enable-ssl --with-mpm=event --with-included-apr", cwd=apache_src_dir)
        run(f"make -j{os.cpu_count()}", cwd=apache_src_dir)
        run("make install", cwd=apache_src_dir)
        good(f"Apache installed locally at {artifact_dir}")

    elif system == "Windows":
        info(f"Configuring Apache for Windows in {artifact_dir}")
        cmake_build_dir = os.path.join(build_dir, "cmake_build")
        os.makedirs(cmake_build_dir, exist_ok=True)
        run(f'cmake ..\\httpd-{apache_latest} -G "Visual Studio 17 2022" -DCMAKE_INSTALL_PREFIX={artifact_dir}', cwd=cmake_build_dir)
        run("cmake --build . --config Release --target INSTALL", cwd=cmake_build_dir)
        good(f"Apache installed locally at {artifact_dir}")

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
