"""The picture box (GUI.md 3): shows part of an image bank.

The picture is the area of image bank IMAGE whose top-left is (U, V), as large
as the box. Programs change the picture with LOAD or IMGSET (or by changing
U / V). Clicks report CLICK and moves with the button held report DRAG, with
the point in MOUSEX / MOUSEY (from the box's top-left).
"""

import pyxel

from .style import COLORS
from .widget import INT, PropertySpec, Widget

COLORS16 = tuple(range(16))


class PictureBox(Widget):
    TYPE = "PICTUREBOX"
    PROPERTIES = (
        PropertySpec("IMAGE", INT, 0, (0, 1, 2)),
        PropertySpec("U", INT, 0),
        PropertySpec("V", INT, 0),
        PropertySpec("COLKEY", INT, -1, (-1,) + COLORS16),
        PropertySpec("BGCOLOR", INT, 0, COLORS16),
        PropertySpec("BORDER", INT, 1, (0, 1)),
        PropertySpec("MOUSEX", INT, 0, readonly=True),
        PropertySpec("MOUSEY", INT, 0, readonly=True),
    )
    EVENTS = ("CLICK", "DRAG")
    DEFAULT_SIZE = (64, 64)

    def __init__(self, name):
        super().__init__(name)
        self._pressed = False

    def _point(self, x, y):
        """Store the point (x, y) (client coordinates) in MOUSEX / MOUSEY. True if it moved."""
        p = self.props
        mx = min(max(0, x - p["X"]), p["W"] - 1)
        my = min(max(0, y - p["Y"]), p["H"] - 1)
        moved = (mx, my) != (p["MOUSEX"], p["MOUSEY"])
        p["MOUSEX"], p["MOUSEY"] = mx, my
        return moved

    def mouse_down(self, x, y):
        self._point(x, y)
        self._pressed = True
        self.fire("CLICK")
        return True

    def mouse_drag(self, x, y):
        if self._pressed and self._point(x, y):
            self.fire("DRAG")

    def mouse_up(self, x, y):
        self._pressed = False

    def draw(self, ui, x, y, focused):
        p = self.props
        w, h = p["W"], p["H"]
        pyxel.rect(x, y, w, h, p["BGCOLOR"])
        if ui.design:
            # The GUI designer: the image banks hold the editor's images, so show a placeholder.
            pyxel.line(x, y, x + w - 1, y + h - 1, COLORS["disabled_fg"])
            pyxel.line(x + w - 1, y, x, y + h - 1, COLORS["disabled_fg"])
            ui.font.draw(x + 3, y + 2, "IMAGE %d" % p["IMAGE"], COLORS["disabled_fg"])
        else:
            ui.clip(x, y, w, h)
            colkey = p["COLKEY"] if p["COLKEY"] >= 0 else None
            pyxel.blt(x, y, p["IMAGE"], p["U"], p["V"], w, h, colkey)
            ui.unclip()
        if p["BORDER"]:
            pyxel.rectb(x, y, w, h, COLORS["border"])
