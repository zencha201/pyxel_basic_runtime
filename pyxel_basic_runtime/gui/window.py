"""A GUI window: title bar, close box and widgets (GUI.md 2).

Widget positions are relative to the client area (below the title bar).
"""

import pyxel

from ..font import LINE_H
from .style import BAR_H, COLORS, SHADOW
from .widget import STR, PropertySpec, Widget
from .widgets import Button, Label

CLOSE_BOX_W = 12


class GuiWindow(Widget):
    """Properties: TITLE, X, Y, W, H (client size), VISIBLE. Event: CLOSE."""

    TYPE = "WINDOW"
    PROPERTIES = (PropertySpec("TITLE", STR, "WINDOW"),)
    EVENTS = ("CLOSE",)
    DEFAULT_SIZE = (160, 100)

    def __init__(self, name, manager):
        super().__init__(name)
        self.manager = manager
        self.props["VISIBLE"] = 0
        self.widgets = []
        self.focus = None
        self._captured = None       # widget that got mouse_down and wants the drag
        self._drag = None           # (dx, dy) while the title bar is dragged

    @property
    def ui(self):
        return self.manager.ui

    def report(self, widget, event):
        """An event of one of this window's widgets."""
        self.manager.fire(widget, event)

    # --- geometry ------------------------------------------------------------
    @property
    def frame_rect(self):
        """The whole window on the screen: border, title bar and client area."""
        x, y, w, h = self.rect
        return x, y, w + 2, h + BAR_H + 1

    @property
    def client_origin(self):
        return self.props["X"] + 1, self.props["Y"] + BAR_H

    def on_frame(self, sx, sy):
        x, y, w, h = self.frame_rect
        return x <= sx < x + w and y <= sy < y + h

    def _on_title(self, sx, sy):
        x, y, w, _ = self.frame_rect
        return x <= sx < x + w and y <= sy < y + BAR_H

    def _on_close_box(self, sx, sy):
        x, y, w, _ = self.frame_rect
        return self._on_title(sx, sy) and sx >= x + w - CLOSE_BOX_W

    def to_client(self, sx, sy):
        ox, oy = self.client_origin
        return sx - ox, sy - oy

    # --- widgets -------------------------------------------------------------
    def add(self, widget):
        widget.window = self
        self.widgets.append(widget)

    def focusables(self):
        return [w for w in self.widgets if w.FOCUSABLE and w.visible and w.enabled]

    def focus_first(self):
        items = self.focusables()
        self.focus = items[0] if items else None

    def focus_next(self, backward=False):
        items = self.focusables()
        if not items:
            self.focus = None
            return
        i = items.index(self.focus) if self.focus in items else -1
        self.focus = items[(i + (-1 if backward else 1)) % len(items)]

    def widget_at(self, x, y):
        for w in reversed(self.widgets):
            if w.visible and w.contains(x, y):
                return w
        return None

    # --- input ---------------------------------------------------------------
    def mouse_down(self, sx, sy):
        if self._on_close_box(sx, sy):
            self.manager.close(self)
            return
        if self._on_title(sx, sy):
            self._drag = (sx - self.props["X"], sy - self.props["Y"])
            return
        x, y = self.to_client(sx, sy)
        widget = self.widget_at(x, y)
        if widget is None or not widget.enabled:
            return
        if widget.FOCUSABLE:
            self.focus = widget
        if widget.mouse_down(x, y):
            self._captured = widget

    def mouse_drag(self, sx, sy):
        if self._drag is not None:
            dx, dy = self._drag
            self.props["X"] = max(-self.props["W"] + 20, min(sx - dx, pyxel.width - 20))
            self.props["Y"] = max(0, min(sy - dy, pyxel.height - BAR_H))
        elif self._captured is not None:
            self._captured.mouse_drag(*self.to_client(sx, sy))

    def mouse_up(self, sx, sy):
        if self._captured is not None:
            self._captured.mouse_up(*self.to_client(sx, sy))
        self._captured = None
        self._drag = None

    def key(self, ev):
        if ev.type == "key" and ev.key == "tab" and not ev.ctrl and not ev.alt:
            self.focus_next(backward=ev.shift)
            return True
        if self.focus is not None and self.focus.visible and self.focus.enabled:
            return self.focus.key(ev)
        return False

    # --- drawing -------------------------------------------------------------
    def draw_window(self, active, at=None, show_focus=True):
        """Draw the window; ``at`` is the frame's top-left (default: its X, Y)."""
        ui = self.ui
        x, y, w, h = self.frame_rect
        if at is not None:
            x, y = at
        pyxel.rect(x + SHADOW, y + SHADOW, w, h, COLORS["shadow"])
        pyxel.rect(x, y, w, h, COLORS["window_bg"])
        pyxel.rectb(x, y, w, h, COLORS["border"])
        pyxel.rect(x + 1, y + 1, w - 2, BAR_H - 1, COLORS["title_bg" if active else "title_inactive_bg"])
        pyxel.clip(x + 1, y + 1, w - 2 - CLOSE_BOX_W, BAR_H - 1)
        ui.font.draw(x + 4, y + 1, self.props["TITLE"], COLORS["title_fg"])
        pyxel.clip()
        ui.font.draw(x + w - CLOSE_BOX_W + 1, y + 1, "×", COLORS["title_fg"])
        self.draw_widgets((x + 1, y + BAR_H), active and show_focus)

    def draw_widgets(self, origin, show_focus):
        ox, oy = origin
        pyxel.clip(ox, oy, self.props["W"], self.props["H"])
        for w in self.widgets:
            if w.visible:
                wx, wy, _, _ = w.rect
                w.draw(self.ui, ox + wx, oy + wy, show_focus and w is self.focus)
        pyxel.clip()


class MessageWindow(GuiWindow):
    """MSGBOX: lines of text and an OK button; closes itself (GUI.md 4)."""

    BUTTON_W = 48

    def __init__(self, manager, text, title):
        super().__init__("", manager)
        font = manager.ui.font
        lines = text.split("\n")
        text_w = max([font.width(s) for s in lines] + [font.width(title) + 20, self.BUTTON_W])
        w = text_w + 16
        h = len(lines) * LINE_H + 8 + 16 + 8
        self.props.update(TITLE=title, W=w, H=h, VISIBLE=1,
                          X=(pyxel.width - w - 2) // 2, Y=max(0, (pyxel.height - h - BAR_H) // 2))
        for i, line in enumerate(lines):
            label = Label("")
            label.props.update(TEXT=line, X=8, Y=6 + i * LINE_H, W=text_w, H=LINE_H)
            self.add(label)
        ok = Button("")
        ok.props.update(TEXT="OK", X=(w - self.BUTTON_W) // 2, Y=h - 16 - 6, W=self.BUTTON_W, H=16)
        self.add(ok)
        self.focus = ok

    def report(self, widget, event):
        if event == "CLICK":
            self.manager.close(self)

    def key(self, ev):
        if ev.type == "key" and ev.key in ("enter", "escape"):
            self.manager.close(self)
            return True
        return super().key(ev)
