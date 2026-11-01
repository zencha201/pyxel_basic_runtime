"""Build pyxel_basic_runtime.pyxapp (BASIC on its own).

    python tools/build_pyxapp.py

main.py and the two packages (pyxel_basic_runtime, and py_basic_core from the
core/ submodule) are copied to a temporary folder, leaving out caches, and
"pyxel package" is run there. The result is written to the repository folder.
"""

import os
import shutil
import subprocess
import sys
import tempfile

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_NAME = "pyxel_basic_runtime"
PACKAGES = (
    os.path.join(REPO_DIR, "pyxel_basic_runtime"),
    os.path.join(REPO_DIR, "core", "py_basic_core"),
)
IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def stage(folder):
    """Copy what the program needs into ``folder``."""
    os.makedirs(folder)
    shutil.copy(os.path.join(REPO_DIR, "main.py"), folder)
    for package in PACKAGES:
        shutil.copytree(package, os.path.join(folder, os.path.basename(package)), ignore=IGNORE)


def build():
    if not os.path.isfile(os.path.join(PACKAGES[1], "__init__.py")):
        raise SystemExit("core/ is empty: run 'git submodule update --init' first")
    with tempfile.TemporaryDirectory() as tmp:
        stage(os.path.join(tmp, APP_NAME))
        subprocess.run(["pyxel", "package", APP_NAME, os.path.join(APP_NAME, "main.py")],
                       cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        target = os.path.join(REPO_DIR, APP_NAME + ".pyxapp")
        shutil.move(os.path.join(tmp, APP_NAME + ".pyxapp"), target)
    print("built " + target)
    return target


if __name__ == "__main__":
    build()
    sys.exit(0)
