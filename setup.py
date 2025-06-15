import os
import sys
import shutil
import zipfile
from setuptools import setup, find_packages
from dotenv import load_dotenv, set_key

APP_NAME = "SCOM"
MAIN_SCRIPT = "window.py"
ICON_PATH = "favicon.ico"
NUITKA_BUILD_DIR = f"{APP_NAME}.build"
REQUIRED_PACKAGES = [
    "pyside6",
    "pyserial",
    "requests",
]

# Load .env file
env_file = ".env"
load_dotenv(env_file)
CURRENT_VERSION = os.getenv("VERSION", "1.0.0")

# Check if the script is run with the --feature argument
IS_FEATURE_BUILD = '--feature' in sys.argv
if IS_FEATURE_BUILD:
    sys.argv.remove('--feature')

def increment_version():
    current_version = os.getenv("VERSION", "1.0.0")
    version_parts = current_version.split(".")
    version_parts[2] = str(int(version_parts[2]) + 1)  # Increment patch version
    new_version = ".".join(version_parts)
    set_key(env_file, "VERSION", new_version)
    print(f"Version updated: {current_version} -> {new_version}")
    return new_version

def create_setup():
    app_name = f"{APP_NAME}-feature" if IS_FEATURE_BUILD else APP_NAME
    
    setup_kwargs = {
        "name": app_name,
        "scripts": [MAIN_SCRIPT],
        "install_requires": REQUIRED_PACKAGES,
        "packages": find_packages(include=['utils', 'utils.*']),
        "package_data": {
            '': ['*.qss'],
        },
    }
    return setup_kwargs

def run_nuitka(version):
    app_name = f"{APP_NAME}-feature" if IS_FEATURE_BUILD else APP_NAME
    build_dir = f"{app_name}.build"
    
    try:
        if os.path.exists(build_dir):
            shutil.rmtree(build_dir)
    except Exception as e:
        print(f"Error while removing build directory: {e}")

    data_dirs = ["styles", "config", "res", "logs", "tmps"]
    include_data_dirs = [
        f"--include-data-dir={data_dir}={data_dir}" for data_dir in data_dirs if os.path.exists(data_dir)
    ]
    
    data_files = [ICON_PATH, ".env", "Help.md", "CHANGELOG.md"]
    include_data_files = [
        f"--include-data-file={file}={file}" for file in data_files if os.path.exists(file)
    ]

    nuitka_command = (
        f"python -m nuitka --plugin-enable=pyside6 "
        f"--follow-import-to=utils --follow-import-to=components "
        f"{' '.join(include_data_dirs)} "
        f"{' '.join(include_data_files)} "
        f"--windows-icon-from-ico={ICON_PATH} "
        f"--mingw64 --standalone --windows-disable-console "
        f"--assume-yes-for-downloads "
        f"--output-dir={build_dir} "
        f"--output-filename={app_name}.exe {MAIN_SCRIPT}"
    )

    print(f"Building {'feature' if IS_FEATURE_BUILD else 'main'} version...")
    print(f"Running Nuitka command: {nuitka_command}")
    
    try:
        result = os.system(nuitka_command)
        if result != 0:
            error_message = f"Nuitka command failed with exit code {result}."
            print(error_message)
            with open('nuitka_error.log', 'w') as log_file:
                log_file.write(error_message)
            exit(result)
    except Exception as e:
        print(f"Error while running Nuitka command: {e}")
        return

    compress_and_cleanup(version, app_name, build_dir)

def compress_and_cleanup(version, app_name, build_dir):
    try:
        dist_dir = os.path.join(build_dir, "window.dist")
        if not os.path.exists(dist_dir):
            print(f"Directory {dist_dir} not found.")
            return

        zip_filename = f"{app_name}-{version}.zip"
        
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)
        
        print(f"Compressed {dist_dir} to {zip_filename}")

        # Cleanup: remove build directory
        shutil.rmtree(build_dir)
        print(f"Removed build directory: {build_dir}")
        
        if os.path.exists("build"):
            shutil.rmtree("build")
            print("Removed build directory: build")

    except Exception as e:
        print(f"Error during compression or cleanup: {e}")

if __name__ == "__main__":
    try:
        setup(**create_setup())
        run_nuitka(CURRENT_VERSION)
        
        # 只在非feature分支时自动递增版本号
        if not IS_FEATURE_BUILD:
            increment_version()
        else:
            print("Feature branch build completed, version not incremented.")
            
    except Exception as e:
        print(f"Error during setup or Nuitka run: {e}")