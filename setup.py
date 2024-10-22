import os
import shutil
from setuptools import setup, find_packages

APP_NAME = "SCOM"
MAIN_SCRIPT = "window.py"
ICON_PATH = "favicon.ico"
REQUIRED_PACKAGES = [
    "pyside6",
    "pyserial",
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

setup(**create_setup())

# Additional code to run Nuitka
nuitka_build_dir = f"{APP_NAME}.build"
if os.path.exists(nuitka_build_dir):
    shutil.rmtree(nuitka_build_dir)

nuitka_command = (
    f"python -m nuitka --plugin-enable=pyside6 "
    f"--follow-import-to=utils --windows-icon-from-ico={ICON_PATH} "
    f"--mingw64 --standalone {MAIN_SCRIPT}"
)

print(f"Running Nuitka command: {nuitka_command}")
result = os.system(nuitka_command)
if result != 0:
    print(f"Nuitka command failed with exit code {result}")
    exit(result)
