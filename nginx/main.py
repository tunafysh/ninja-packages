from pathlib import Path
from util import *

def clone_nginx():
    repo_url = "https://github.com/nginx/nginx.git"
    if os.path.exists(Path.cwd() / "build" / "nginx"):
        info("nginx source already exists, skipping clone")
    else:     
        run(f"git clone {repo_url}", cwd=Path.cwd() / "build")

def unix_build(nginx_src, artifact_dir):
    if not os.path.exists("/usr/lib/libpcre.so"):
        err("libpcre is not installed. Please install it and try again.")
        sys.exit(1)
    if not os.path.exists("/usr/lib/libssl.so"):
        err("libssl is not installed. Please install it and try again.")
        sys.exit(1)
    if not os.path.exists("/usr/lib/libz.so"):
        err("zlib is not installed. Please install it and try again.")
        sys.exit(1)
    
    if not tool_exists("gcc"):
        err("gcc is not installed. Please install it and try again.")
        sys.exit(1)
    
    if not tool_exists("make"): 
        err("make is not installed. Please install it and try again.")
        sys.exit(1)

    configure_cmd = f"./configure --prefix={artifact_dir} --with-pcre --with-openssl --with-zlib"
    run(configure_cmd, cwd=nginx_src)
    run(f"make -j{os.cpu_count()}", cwd=nginx_src)
    run("make install", cwd=nginx_src)
    good(f"nginx built and installed locally at {artifact_dir}")

def windows_build(nginx_src, artifact_dir):
    winget_is_available = tool_exists("winget")
    if not tool_exists("cmake"):
        err("CMake is not installed. Please install it and try again.")
        sys.exit(1)
    if not tool_exists("msbuild"):
        err("MSBuild is not installed. Please install Visual Studio and try again.")
        sys.exit(1)
    if not tool_exists("vcpkg"):
        err("vcpkg is not installed. Please install vcpkg and try again.")
        sys.exit(1)
    if not tool_exists("perl"):
        if winget_is_available:
            warn("Perl is not installed. Attempting to install Strawberry Perl via winget...")
            run("winget install --id=StrawberryPerl.StrawberryPerl --source=winget")
            if not tool_exists("perl"):
                err("Failed to install Perl via winget. Please install Perl manually and try again.")
                sys.exit(1)
        err("Perl is not installed. Please install Perl and try again.")
        sys.exit(1)

    # Create vcpkg manifest
    vcpkg_json = os.path.join(nginx_src, "vcpkg.json")
    write_file(
        vcpkg_json,
        """{
  "name": "nginx-build",
  "version": "1.0.0",
  "dependencies": [
    "openssl",
    "pcre",
    "zlib"
  ]
}"""
    )

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

    import os
import shutil
import subprocess
import urllib.request
import zipfile

def info(msg):
    print(f"[INFO] {msg}")

def run(cmd, cwd=None):
    info(f"Running: {cmd}")
    subprocess.run(cmd, shell=True, check=True, cwd=cwd)

def write_file(path, content):
    with open(path, "w") as f:
        f.write(content)

# --- CONFIG ---
build_dir = os.path.abspath("build")
nginx_version = "1.26.1"
nginx_src = os.path.join(build_dir, f"nginx-{nginx_version}")
shuriken_dir = os.path.join(build_dir, "nginx_shuriken")

# --- STEP 1: Download Nginx ---
os.makedirs(build_dir, exist_ok=True)
nginx_zip = os.path.join(build_dir, f"nginx-{nginx_version}.zip")
if not os.path.exists(nginx_zip):
    info(f"Downloading Nginx {nginx_version}...")
    urllib.request.urlretrieve(f"http://nginx.org/download/nginx-{nginx_version}.zip", nginx_zip)

# --- STEP 2: Extract ---
if not os.path.exists(nginx_src):
    info("Extracting Nginx...")
    with zipfile.ZipFile(nginx_zip, "r") as zip_ref:
        zip_ref.extractall(build_dir)

# --- STEP 3: vcpkg manifest ---
vcpkg_json = os.path.join(nginx_src, "vcpkg.json")
write_file(
    vcpkg_json,
    """{
  "name": "nginx-build",
  "version": "1.0.0",
  "dependencies": [
    "openssl",
    "pcre",
    "zlib"
  ]
}"""
)

info("Installing dependencies via vcpkg...")
run("vcpkg install", cwd=nginx_src)

# --- STEP 4: Set INCLUDE/LIB environment variables ---
inc_path = os.path.join(nginx_src, "installed", "x64-windows", "include")
lib_path = os.path.join(nginx_src, "installed", "x64-windows", "lib")
os.environ["INCLUDE"] = f"{inc_path};" + os.environ.get("INCLUDE", "")
os.environ["LIB"] = f"{lib_path};" + os.environ.get("LIB", "")

# --- STEP 5: Build Nginx with nmake ---
info("Building Nginx with nmake...")
# Open Developer Command Prompt first before running Python
run("nmake -f objs/Makefile.msvc", cwd=nginx_src)

# --- STEP 6: Package shuriken ---
info("Packaging shuriken...")
if os.path.exists(shuriken_dir):
    shutil.rmtree(shuriken_dir)
os.makedirs(shuriken_dir, exist_ok=True)

# Copy nginx.exe
shutil.copy(os.path.join(nginx_src, "objs", "nginx.exe"), shuriken_dir)
# Copy conf folder
shutil.copytree(os.path.join(nginx_src, "conf"), os.path.join(shuriken_dir, "conf"))
# Copy DLLs
dlls = ["libcrypto-1_1-x64.dll", "libssl-1_1-x64.dll", "zlib1.dll"]
for dll in dlls:
    dll_path = os.path.join(inc_path.replace("include", "bin"), dll)
    if os.path.exists(dll_path):
        shutil.copy(dll_path, shuriken_dir)

info(f"Nginx shuriken ready at {shuriken_dir}")


def main():
    system = platform.system()
    project_root = Path.cwd() / "nginx"
    build_dir = project_root / "build"
    artifact_dir = project_root / "artifact"

    build_dir.mkdir(parents=True, exist_ok=True)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    info(f"Working directory: {build_dir}")
    info(f"Artifact directory: {artifact_dir}")

    clone_nginx()

    info(f"Building nginx on {system}")

    if system in ("Linux", "Darwin", "FreeBSD"):
        unix_build(build_dir / "nginx", artifact_dir)
    elif system == "Windows":
        windows_build(build_dir / "nginx", artifact_dir)
    else:
        err(f"Unsupported platform: {system}")
        sys.exit(1)



if __name__ == "__main__":
    main()