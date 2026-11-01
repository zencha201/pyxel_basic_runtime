"""Load this folder's package as ``basic`` and start one headless BasicApp.

The package is used as ``basic`` inside an editor and also on its own under
any folder name, so the tests do not rely on the folder name.
pyxel.init() may be called only once per process: the session's BasicApp
does it, and every test uses that Pyxel.
"""

import importlib.util
import os
import sys

import pytest

PACKAGE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PACKAGE = "basic"

if PACKAGE not in sys.modules:
    _spec = importlib.util.spec_from_file_location(
        PACKAGE, os.path.join(PACKAGE_DIR, "__init__.py"), submodule_search_locations=[PACKAGE_DIR])
    _module = importlib.util.module_from_spec(_spec)
    sys.modules[PACKAGE] = _module
    _spec.loader.exec_module(_module)


class QuitRecorder:
    def __init__(self):
        self.count = 0

    def __call__(self):
        self.count += 1


@pytest.fixture(scope="session")
def basic_app():
    from basic.app import BasicApp
    return BasicApp(headless=True, quit=QuitRecorder())


@pytest.fixture(autouse=True)
def pyxel_ready(basic_app):
    return basic_app
