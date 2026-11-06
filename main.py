"""Start-up script: python main.py [program.bas]

Runs the BASIC program when a file is given, otherwise starts direct mode.
The package retro_basic_runtime is in this folder and py_basic_core in the
core/ submodule; in a .pyxapp both sit next to this file.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _folder in (os.path.join(HERE, "core"), HERE):
    if os.path.isdir(_folder) and _folder not in sys.path:
        sys.path.insert(0, _folder)

from retro_basic_runtime.app import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
