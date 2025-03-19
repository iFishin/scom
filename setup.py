import os
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

def increment_version():
    current_version = os.getenv("VERSION", "1.0.0")
    version_parts = current_version.split(".")
    version_parts[2] = str(int(version_parts[2]) + 1)  # Increment patch version
    new_version = ".".join(version_parts)
    set_key(env_file, "VERSION", new_version)
    print(f"Version updated: {current_version} -> {new_version}")
    return new_version

def create_setup():
    setup_kwargs = {
        "name": APP_NAME,
        "scripts": [MAIN_SCRIPT],
        "install_requires": REQUIRED_PACKAGES,
        "packages": find_packages(include=['utils', 'utils.*']),
        "package_data": {
            '': ['*.qss'],
        },
    }
    return setup_kwargs

def run_nuitka(version):
    try:
        if os.path.exists(NUITKA_BUILD_DIR):
            shutil.rmtree(NUITKA_BUILD_DIR)
    except Exception as e:
        print(f"Error while removing build directory: {e}")

    data_dirs = ["styles", "config", "res", "logs", "tmps"]
    include_data_dirs = [
        f"--include-data-dir={data_dir}={data_dir}" for data_dir in data_dirs if os.path.exists(data_dir)
    ]

    nuitka_command = (
        f"python -m nuitka --plugin-enable=pyside6 "
        f"--follow-import-to=utils --follow-import-to=components "
        f"{' '.join(include_data_dirs)} "
        f"--include-data-file={ICON_PATH}={ICON_PATH} "
        f"--windows-icon-from-ico={ICON_PATH} "
        f"--mingw64 --standalone --windows-disable-console "
        f"--assume-yes-for-downloads "
        f"--output-dir={NUITKA_BUILD_DIR} "
        f"--output-filename={APP_NAME}.exe {MAIN_SCRIPT}"
    )

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

    compress_and_cleanup(version)

def compress_and_cleanup(version):
    try:
        dist_dir = os.path.join(NUITKA_BUILD_DIR, "window.dist")
        if not os.path.exists(dist_dir):
            print(f"Directory {dist_dir} not found.")
            return

        zip_filename = f"{APP_NAME}-{version}.zip"
        with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(dist_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, dist_dir)
                    zipf.write(file_path, arcname)
        print(f"Compressed {dist_dir} to {zip_filename}")

        # Cleanup: remove build directory
        shutil.rmtree(NUITKA_BUILD_DIR)
        print(f"Removed build directory: {NUITKA_BUILD_DIR}")
        shutil.rmtree("build")
        print("Removed build directory: build")

    except Exception as e:
        print(f"Error during compression or cleanup: {e}")

if __name__ == "__main__":
    try:
        setup(**create_setup())
        run_nuitka(CURRENT_VERSION)
        increment_version()
    except Exception as e:
        print(f"Error during setup or Nuitka run: {e}")
