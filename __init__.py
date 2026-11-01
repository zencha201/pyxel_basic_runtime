"""BASIC on Pyxel: the BASIC screen and the Pyxel commands (DESIGN.md 1).

The language itself is the ``core`` sub-package, which does not use Pyxel.
All imports inside the package are relative, so it works under any folder
name (for example as ``basic`` inside an editor, or on its own).
"""

from .font import Font
from .input import Event, Input
from .screen import (DIRECT, ENDED, ERROR, EXITED, PROGRAM, STOPPED, BasicResult, BasicScreen,
                     default_font)

__all__ = [
    "Font", "Event", "Input", "BasicResult", "BasicScreen", "default_font",
    "PROGRAM", "DIRECT", "ENDED", "ERROR", "STOPPED", "EXITED",
]
