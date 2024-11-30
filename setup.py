import os
import shutil
from setuptools import setup, find_packages

APP_NAME = "SCOM"
MAIN_SCRIPT = "window.py"
ICON_PATH = "favicon.ico"
REQUIRED_PACKAGES = [
    "pyside6",
    "pyserial",
    "requests",
]

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

def run_nuitka():
    nuitka_build_dir = f"{APP_NAME}.build"
    if os.path.exists(nuitka_build_dir):
        shutil.rmtree(nuitka_build_dir)

    data_dirs = ["styles", "config", "res", "logs", "tmps"]
    include_data_dirs = " ".join([f"--include-data-dir={d}={d}" for d in data_dirs])

    nuitka_command = (
        f"python -m nuitka --plugin-enable=pyside6 "
        f"--follow-import-to=utils "
        f"--follow-import-to=components "
        f"{include_data_dirs} "
        f"--include-data-file={ICON_PATH}={ICON_PATH} "
        f"--windows-icon-from-ico={ICON_PATH} "
        f"--mingw64 --standalone --windows-disable-console "
        f"--output-dir={nuitka_build_dir} "
        f"--output-filename={APP_NAME}.exe {MAIN_SCRIPT}"
    )

    print(f"Running Nuitka command: {nuitka_command}")
    result = os.system(nuitka_command)
    if result != 0:
        print(f"Nuitka command failed with exit code {result}")
        exit(result)

if __name__ == "__main__":
    setup(**create_setup())
    run_nuitka()
