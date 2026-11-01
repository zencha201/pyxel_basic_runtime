"""Build basic.pyxapp (BASIC on its own) without tests, documents and git files.

    python tools/build_pyxapp.py

The package folder is copied to a temporary folder named "basic" with only
what the program needs, and "pyxel package" is run there. The result is
written to the package folder.
"""

import os
import shutil
import subprocess
import sys
import tempfile

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE_NAME = "basic"

# Left out of the package (names anywhere in the tree).
EXCLUDED_DIRS = {"tests", "tools", "__pycache__", ".git", ".pytest_cache"}
EXCLUDED_FILES = {".git", ".gitmodules", ".gitignore", "pytest.ini", "LICENSE"}
EXCLUDED_SUFFIXES = (".md", ".pyxapp", ".pyc")


def ignore(folder, names):
    return [n for n in names
            if n in EXCLUDED_DIRS or n in EXCLUDED_FILES or n.endswith(EXCLUDED_SUFFIXES)]


def build(output_dir=PACKAGE_DIR):
    if not os.path.isfile(os.path.join(PACKAGE_DIR, "core", "__init__.py")):
        raise SystemExit("core/ is empty: run 'git submodule update --init' first")
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(PACKAGE_DIR, os.path.join(tmp, PACKAGE_NAME), ignore=ignore)
        subprocess.run(["pyxel", "package", PACKAGE_NAME, os.path.join(PACKAGE_NAME, "main.py")],
                       cwd=tmp, check=True, stdout=subprocess.DEVNULL)
        target = os.path.join(output_dir, PACKAGE_NAME + ".pyxapp")
        shutil.move(os.path.join(tmp, PACKAGE_NAME + ".pyxapp"), target)
    print("built " + target)
    return target


if __name__ == "__main__":
    build()
    sys.exit(0)
