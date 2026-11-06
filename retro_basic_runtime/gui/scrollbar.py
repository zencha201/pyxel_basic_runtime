"""Horizontal and vertical scroll bars (GUI.md 3).

A scroll bar has arrow buttons at both ends, a track and a thumb. VALUE goes
from MIN to MAX; the arrows move it by STEP, a click on the track by PAGE, and
the thumb can be dragged. The list box uses the same class for its own bar.
"""

import pyxel

from .style import COLORS, KEY_HOLD, KEY_REPEAT, SCROLLBAR_W, fill, triangle
from .widget import INT, PropertySpec, Widget, bgcolor_property

MIN_THUMB = 6


class ScrollBar(Widget):
    PROPERTIES = (
        PropertySpec("VALUE", INT, 0),
        PropertySpec("MIN", INT, 0),
        PropertySpec("MAX", INT, 100),
        PropertySpec("STEP", INT, 1),
        PropertySpec("PAGE", INT, 10),
        bgcolor_property(COLORS["scroll_track"]),        # the track
    )
    EVENTS = ("CHANGE",)
    FOCUSABLE = True
    VERTICAL = False

    def __init__(self, name, on_change=None):
        super().__init__(name)
        self.on_change = on_change      # used instead of the CHANGE event when given
        self._part = None               # "dec" / "inc" / "pgdec" / "pginc" / "thumb" while pressed
        self._grab = 0                  # where the thumb was grabbed
        self._mouse = 0                 # mouse position along the bar while pressed
        self._hold = 0

    # --- value -----------------------------------------------------------------
    @property
    def low(self):
        return self.props["MIN"]

    @property
    def high(self):
        return max(self.props["MIN"], self.props["MAX"])

    def check(self, name, value):
        if name == "VALUE":
            return min(max(value, self.low), self.high)
        if name in ("STEP", "PAGE"):
            return max(1, value)
        return value

    def changed(self, name):
        if name in ("MIN", "MAX"):
            self.props["VALUE"] = min(max(self.props["VALUE"], self.low), self.high)

    def scroll_to(self, value):
        """Set VALUE as the user does: reports CHANGE when it changes."""
        value = min(max(value, self.low), self.high)
        if value == self.props["VALUE"]:
            return
        self.props["VALUE"] = value
        if self.on_change is not None:
            self.on_change(value)
        else:
            self.fire("CHANGE")

    # --- geometry (along the bar, in the coordinates of the mouse methods) -------
    def _along(self, x, y):
        return y if self.VERTICAL else x

    def _span(self):
        """(start, length) of the whole bar along its direction."""
        p = self.props
        return (p["Y"], p["H"]) if self.VERTICAL else (p["X"], p["W"])

    def _track(self):
        start, length = self._span()
        return start + SCROLLBAR_W, max(1, length - 2 * SCROLLBAR_W)

    def _thumb(self):
        """(start, size) of the thumb."""
        ts, tl = self._track()
        page = self.props["PAGE"]
        size = min(tl, max(MIN_THUMB, tl * page // (self.high - self.low + page)))
        if self.high == self.low:
            return ts, tl
        return ts + (tl - size) * (self.props["VALUE"] - self.low) // (self.high - self.low), size

    # --- input -----------------------------------------------------------------
    def _step(self):
        value, part = self.props["VALUE"], self._part
        if part == "dec":
            self.scroll_to(value - self.props["STEP"])
        elif part == "inc":
            self.scroll_to(value + self.props["STEP"])
        elif part in ("pgdec", "pginc"):
            start, size = self._thumb()
            if part == "pgdec" and self._mouse < start:
                self.scroll_to(value - self.props["PAGE"])
            elif part == "pginc" and self._mouse >= start + size:
                self.scroll_to(value + self.props["PAGE"])

    def mouse_down(self, x, y):
        start, length = self._span()
        m = self._along(x, y)
        thumb, size = self._thumb()
        if m < start + SCROLLBAR_W:
            self._part = "dec"
        elif m >= start + length - SCROLLBAR_W:
            self._part = "inc"
        elif m < thumb:
            self._part = "pgdec"
        elif m >= thumb + size:
            self._part = "pginc"
        else:
            self._part = "thumb"
            self._grab = m - thumb
        self._mouse = m
        self._hold = 0
        if self._part != "thumb":
            self._step()
        return True

    def mouse_drag(self, x, y):
        self._mouse = self._along(x, y)
        if self._part != "thumb":
            return
        ts, tl = self._track()
        _, size = self._thumb()
        room = tl - size
        if room > 0:
            offset = self._mouse - self._grab - ts
            self.scroll_to(self.low + round(offset * (self.high - self.low) / room))

    def mouse_up(self, x, y):
        self._part = None

    def update(self, frame):
        if self._part not in (None, "thumb"):
            self._hold += 1
            if self._hold >= KEY_HOLD and (self._hold - KEY_HOLD) % KEY_REPEAT == 0:
                self._step()

    def wheel(self, dy):
        self.scroll_to(self.props["VALUE"] - dy * self.props["STEP"])
        return True

    def key(self, ev):
        if ev.type != "key" or ev.ctrl or ev.alt:
            return False
        back, forward = ("up", "down") if self.VERTICAL else ("left", "right")
        value, step, page = self.props["VALUE"], self.props["STEP"], self.props["PAGE"]
        moves = {back: value - step, forward: value + step, "pageup": value - page,
                 "pagedown": value + page, "home": self.low, "end": self.high}
        if ev.key not in moves:
            return False
        self.scroll_to(moves[ev.key])
        return True

    # --- drawing ---------------------------------------------------------------
    def draw(self, ui, x, y, focused):
        w, h = self.props["W"], self.props["H"]
        thumb = COLORS["scroll_thumb"]
        arrow = COLORS["scroll_track"] if self.enabled else COLORS["disabled_fg"]
        fill(x, y, w, h, self.props["BGCOLOR"])
        # The thumb's position relative to the bar's own top-left.
        ts, size = self._thumb()
        ts -= self._span()[0]
        if self.VERTICAL:
            pyxel.rect(x, y, w, SCROLLBAR_W, thumb)
            pyxel.rect(x, y + h - SCROLLBAR_W, w, SCROLLBAR_W, thumb)
            cx = x + (w - 5) // 2
            triangle(cx, y + 2, "up", arrow)
            triangle(cx, y + h - SCROLLBAR_W + 2, "down", arrow)
            pyxel.rect(x + 1, y + ts + 1, max(1, w - 2), max(1, size - 2), thumb)
        else:
            pyxel.rect(x, y, SCROLLBAR_W, h, thumb)
            pyxel.rect(x + w - SCROLLBAR_W, y, SCROLLBAR_W, h, thumb)
            cy = y + (h - 5) // 2
            triangle(x + 2, cy, "left", arrow)
            triangle(x + w - SCROLLBAR_W + 2, cy, "right", arrow)
            pyxel.rect(x + ts + 1, y + 1, max(1, size - 2), max(1, h - 2), thumb)
        if focused:
            pyxel.rectb(x, y, w, h, COLORS["focus"])


class HScrollBar(ScrollBar):
    TYPE = "HSCROLLBAR"
    DEFAULT_SIZE = (80, SCROLLBAR_W)


class VScrollBar(ScrollBar):
    TYPE = "VSCROLLBAR"
    DEFAULT_SIZE = (SCROLLBAR_W, 60)
    VERTICAL = True
