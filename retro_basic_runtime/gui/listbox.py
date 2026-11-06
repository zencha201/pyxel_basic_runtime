"""The list box (GUI.md 3): a list of items with one selected, and a scroll bar.

ITEMS holds the items separated by CHR$(10) ("" is an empty list). INDEX is the
selected item from 0, or -1 for none. ITEM (the selected text) and COUNT are
read-only.
"""

import pyxel

from ..font import LINE_H
from .scrollbar import VScrollBar
from .style import COLORS, SCROLLBAR_W, fill
from .widget import INT, STR, PropertyError, PropertySpec, Widget, bgcolor_property

DOUBLE_CLICK_FRAMES = 20
TEXT_PAD = 3


class ListBox(Widget):
    TYPE = "LISTBOX"
    PROPERTIES = (
        PropertySpec("ITEMS", STR, ""),
        PropertySpec("INDEX", INT, -1),
        PropertySpec("ITEM", STR, "", readonly=True),
        PropertySpec("COUNT", INT, 0, readonly=True),
        bgcolor_property(COLORS["field_bg"]),
    )
    EVENTS = ("CHANGE", "ENTER")
    DEFAULT_SIZE = (80, 56)
    FOCUSABLE = True

    def __init__(self, name):
        super().__init__(name)
        self.top = 0                    # first item shown
        self._last_click = (None, -1)   # (frame, index) of the last click, for double clicks
        self._bar_pressed = False       # the mouse went down on the scroll bar
        self.bar = VScrollBar("", on_change=self._scrolled)

    # --- items -----------------------------------------------------------------
    @property
    def items(self):
        text = self.props["ITEMS"]
        return text.split("\n") if text else []

    @property
    def rows(self):
        return max(1, (self.props["H"] - 4) // LINE_H)

    def check(self, name, value):
        if name == "INDEX" and not -1 <= value < len(self.items):
            raise PropertyError("value", "INDEX=%d" % value)
        return value

    def changed(self, name):
        if name == "ITEMS" and self.props["INDEX"] >= len(self.items):
            self.props["INDEX"] = -1
        if name in ("ITEMS", "INDEX"):
            self._update_item()
            if name == "INDEX":
                self._show_selected()
            self._clamp_top()

    def _update_item(self):
        items, index = self.items, self.props["INDEX"]
        self.props["COUNT"] = len(items)
        self.props["ITEM"] = items[index] if 0 <= index < len(items) else ""

    def _clamp_top(self):
        self.top = min(max(0, self.top), max(0, len(self.items) - self.rows))

    def _show_selected(self):
        index = self.props["INDEX"]
        if index < 0:
            return
        if index < self.top:
            self.top = index
        elif index >= self.top + self.rows:
            self.top = index - self.rows + 1

    def select(self, index):
        """Select as the user does: reports CHANGE when the selection changes."""
        items = self.items
        if not items:
            return
        index = min(max(0, index), len(items) - 1)
        if index != self.props["INDEX"]:
            self.props["INDEX"] = index
            self._update_item()
            self.fire("CHANGE")
        self._show_selected()
        self._clamp_top()

    # --- the scroll bar ----------------------------------------------------------
    def _layout_bar(self):
        """Place the bar at the right edge, in the same coordinates as the list box."""
        p, bar = self.props, self.bar
        bar.props.update(X=p["X"] + p["W"] - SCROLLBAR_W - 1, Y=p["Y"] + 1,
                         W=SCROLLBAR_W, H=max(1, p["H"] - 2), ENABLED=p["ENABLED"],
                         MIN=0, MAX=max(0, len(self.items) - self.rows), PAGE=self.rows,
                         VALUE=self.top)

    def _scrolled(self, value):
        self.top = value

    def _on_bar(self, x, y):
        self._layout_bar()
        return self.bar.contains(x, y)

    # --- input -----------------------------------------------------------------
    def mouse_down(self, x, y):
        if self._on_bar(x, y):
            self._bar_pressed = True
            return self.bar.mouse_down(x, y)
        self._bar_pressed = False
        row = (y - self.props["Y"] - 2) // LINE_H
        index = self.top + row
        if 0 <= row < self.rows and index < len(self.items):
            self.select(index)
            frame = self.window.ui.frame if self.window is not None else 0
            last_frame, last_index = self._last_click
            if (last_index == index and last_frame is not None
                    and frame - last_frame <= DOUBLE_CLICK_FRAMES):
                self.fire("ENTER")
                frame = None                # a third click starts again
            self._last_click = (frame, index)
        return False

    def mouse_drag(self, x, y):
        if self._bar_pressed:
            self._layout_bar()
            self.bar.mouse_drag(x, y)

    def mouse_up(self, x, y):
        if self._bar_pressed:
            self.bar.mouse_up(x, y)
        self._bar_pressed = False

    def update(self, frame):
        if self._bar_pressed:
            self._layout_bar()
            self.bar.update(frame)

    def wheel(self, dy):
        self.top -= dy * 3
        self._clamp_top()
        return True

    def key(self, ev):
        if ev.type != "key" or ev.ctrl or ev.alt:
            return False
        index, n = self.props["INDEX"], len(self.items)
        moves = {"up": index - 1, "down": index + 1, "pageup": index - self.rows,
                 "pagedown": index + self.rows, "home": 0, "end": n - 1}
        if ev.key in moves:
            self.select(moves[ev.key])
        elif ev.key == "enter" and index >= 0:
            self.fire("ENTER")
        else:
            return False
        return True

    # --- drawing ---------------------------------------------------------------
    def draw(self, ui, x, y, focused):
        font = ui.font
        w, h = self.props["W"], self.props["H"]
        fill(x, y, w, h, self.props["BGCOLOR"])
        pyxel.rectb(x, y, w, h, COLORS["focus"] if focused else COLORS["border"])
        items, index = self.items, self.props["INDEX"]
        fg = COLORS["field_fg"] if self.enabled else COLORS["disabled_fg"]
        text_w = w - SCROLLBAR_W - 3
        ui.clip(x + 1, y + 1, text_w, h - 2)
        for row in range(self.rows):
            i = self.top + row
            if i >= len(items):
                break
            ry = y + 2 + row * LINE_H
            color = fg
            if i == index:
                pyxel.rect(x + 1, ry, text_w, LINE_H, COLORS["list_sel_bg"])
                color = COLORS["list_sel_fg"]
            font.draw(x + TEXT_PAD, ry + 1, items[i], color)
        ui.unclip()
        self._layout_bar()
        self.bar.draw(ui, x + w - SCROLLBAR_W - 1, y + 1, False)
