"""BASIC on Pyxel: the BASIC screen and the Pyxel commands (DESIGN.md 1).

The language itself is the ``py_basic_core`` package (a separate repository,
included as the ``core`` submodule), which does not use Pyxel. Both packages
must be importable: put this repository's folder and ``core/`` on sys.path
(main.py and the tests do so).
"""

from .font import Font
from .input import Event, Input
from .screen import (DIRECT, ENDED, ERROR, EXITED, PROGRAM, STOPPED, BasicResult, BasicScreen,
                     default_font)

__all__ = [
    "Font", "Event", "Input", "BasicResult", "BasicScreen", "default_font",
    "PROGRAM", "DIRECT", "ENDED", "ERROR", "STOPPED", "EXITED",
]
