"""Start-up script: python main.py [program.bas]

Runs the BASIC program when a file is given, otherwise starts direct mode.
The package is loaded from this folder whatever the folder is called.
"""

import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PACKAGE = "basic"


def load_package():
    if PACKAGE in sys.modules:
        return sys.modules[PACKAGE]
    spec = importlib.util.spec_from_file_location(
        PACKAGE, os.path.join(HERE, "__init__.py"), submodule_search_locations=[HERE])
    module = importlib.util.module_from_spec(spec)
    sys.modules[PACKAGE] = module
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    load_package()
    from basic.app import main
    sys.exit(main())
