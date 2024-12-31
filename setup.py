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
    try:
        # 添加调试输出，确认路径是否正确
        print(f"Checking build directory: {nuitka_build_dir}")
        if os.path.exists(nuitka_build_dir):
            shutil.rmtree(nuitka_build_dir)
    except Exception as e:
        print(f"Error while checking/removing build directory: {e}")

    data_dirs = ["styles", "config", "res", "logs", "tmps"]
    include_data_dirs = []
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            include_data_dirs.append(f"--include-data-dir={data_dir}={data_dir}")
        else:
            print(f"Directory {data_dir} not found.")
    include_data_dirs_str = " ".join(include_data_dirs)

    nuitka_command = (
        f"python -m nuitka --plugin-enable=pyside6 "
        f"--follow-import-to=utils --follow-import-to=components "
        f"{include_data_dirs_str} "
        f"--include-data-file={ICON_PATH}={ICON_PATH} "
        f"--windows-icon-from-ico={ICON_PATH} "
        f"--mingw64 --standalone --windows-disable-console "
        f"--output-dir={nuitka_build_dir} "
        f"--output-filename={APP_NAME}.exe {MAIN_SCRIPT}"
    )

    print(f"Running Nuitka command: {nuitka_command}")
    try:
        result = os.system(nuitka_command)
        if result!= 0:
            error_message = f"Nuitka command failed with exit code {result}. Command: {nuitka_command}"
            print(error_message)
            with open('nuitka_error.log', 'w') as log_file:
                log_file.write(error_message)
            exit(result)
    except Exception as e:
        print(f"Error while running Nuitka command: {e}")

if __name__ == "__main__":
    try:
        setup(**create_setup())
        run_nuitka()
    except Exception as e:
        print(f"Error during setup or Nuitka run: {e}")