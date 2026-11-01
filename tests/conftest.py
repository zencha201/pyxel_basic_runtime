"""Make pyxel_basic_runtime and py_basic_core importable and start one headless BasicApp.

pyxel.init() may be called only once per process: the session's BasicApp
does it, and every test uses that Pyxel.
"""

import os
import sys

import pytest

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _folder in (os.path.join(REPO_DIR, "core"), REPO_DIR):
    if _folder not in sys.path:
        sys.path.insert(0, _folder)


class QuitRecorder:
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1


@pytest.fixture(scope="session")
def basic_app():
    from pyxel_basic_runtime.app import BasicApp
    return BasicApp(headless=True, quit=QuitRecorder())


@pytest.fixture(autouse=True)
def pyxel_ready(basic_app):
    return basic_app
