"""The standard widgets (GUI.md 3): button, check box, radio button, label,
text field and text area. They are registered like any added widget."""

import pyxel

from ..font import LINE_H
from .registry import register_widget
from .style import BOX, COLORS, check_mark
from .widget import INT, STR, PropertySpec, Widget

INNER_PAD = 3
BLINK_FRAMES = 30


def text_color(widget):
    return COLORS["window_fg"] if widget.enabled else COLORS["disabled_fg"]


@register_widget
class Button(Widget):
    TYPE = "BUTTON"
    PROPERTIES = (PropertySpec("TEXT", STR, "BUTTON"),)
    EVENTS = ("CLICK",)
    DEFAULT_SIZE = (60, 16)
    FOCUSABLE = True

    def __init__(self, name):
        super().__init__(name)
        self.pressed = False
        self._inside = False

    def mouse_down(self, x, y):
        self.pressed = self._inside = True
        return True

    def mouse_drag(self, x, y):
        self._inside = self.contains(x, y)

    def mouse_up(self, x, y):
        if self.pressed and self.contains(x, y):
            self.fire("CLICK")
        self.pressed = self._inside = False

    def key(self, ev):
        if (ev.type == "key" and ev.key == "enter") or (ev.type == "text" and ev.text == " "):
            self.fire("CLICK")
            return True
        return False

    def draw(self, ui, x, y, focused):
        w, h = self.props["W"], self.props["H"]
        off = 1 if self.pressed and self._inside else 0
        if not off:
            pyxel.rect(x + 1, y + 1, w, h, COLORS["shadow"])
        pyxel.rect(x + off, y + off, w, h, COLORS["window_bg"])
        frame = COLORS["focus"] if focused else COLORS["border"]
        pyxel.rectb(x + off, y + off, w, h, frame)
        if focused:
            pyxel.rectb(x + off + 1, y + off + 1, w - 2, h - 2, frame)
        text = ui.font.displayable(self.props["TEXT"])
        tx = x + off + (w - ui.font.width(text)) // 2
        ui.font.draw(tx, y + off + (h - LINE_H) // 2 + 1, text, text_color(self))


@register_widget
class CheckBox(Widget):
    TYPE = "CHECKBOX"
    PROPERTIES = (PropertySpec("TEXT", STR, "CHECK"), PropertySpec("VALUE", INT, 0, (0, 1)))
    EVENTS = ("CHANGE",)
    DEFAULT_SIZE = (60, 15)
    FOCUSABLE = True

    def toggle(self):
        self.props["VALUE"] = 1 - self.props["VALUE"]
        self.fire("CHANGE")

    def mouse_down(self, x, y):
        self.toggle()
        return False

    def key(self, ev):
        if ev.type == "text" and ev.text == " ":
            self.toggle()
            return True
        return False

    def draw(self, ui, x, y, focused):
        by = y + (self.props["H"] - BOX) // 2
        pyxel.rect(x, by, BOX, BOX, COLORS["field_bg"])
        pyxel.rectb(x, by, BOX, BOX, COLORS["focus"] if focused else COLORS["border"])
        if self.props["VALUE"]:
            check_mark(x + 1, by + 2, text_color(self))
        ty = y + (self.props["H"] - LINE_H) // 2 + 1
        ui.font.draw(x + BOX + 3, ty, self.props["TEXT"], text_color(self))


@register_widget
class RadioButton(Widget):
    """Only one radio button with the same GROUP in a window is on."""

    TYPE = "RADIO"
    PROPERTIES = (PropertySpec("TEXT", STR, "RADIO"), PropertySpec("VALUE", INT, 0, (0, 1)),
                  PropertySpec("GROUP", STR, "GROUP1"))
    EVENTS = ("CHANGE",)
    DEFAULT_SIZE = (60, 15)
    FOCUSABLE = True

    def select(self):
        if self.props["VALUE"]:
            return
        self.props["VALUE"] = 1
        self.changed("VALUE")
        self.fire("CHANGE")

    def changed(self, name):
        """Turning one on turns the others of the group off."""
        if name == "VALUE" and self.props["VALUE"] and self.window is not None:
            for other in self.window.widgets:
                if (other is not self and isinstance(other, RadioButton)
                        and other.props["GROUP"] == self.props["GROUP"] and other.props["VALUE"]):
                    other.props["VALUE"] = 0
                    other.fire("CHANGE")

    def mouse_down(self, x, y):
        self.select()
        return False

    def key(self, ev):
        if ev.type == "text" and ev.text == " ":
            self.select()
            return True
        return False

    def draw(self, ui, x, y, focused):
        by = y + (self.props["H"] - BOX) // 2
        cx, cy = x + BOX // 2, by + BOX // 2
        pyxel.circ(cx, cy, BOX // 2, COLORS["field_bg"])
        pyxel.circb(cx, cy, BOX // 2, COLORS["focus"] if focused else COLORS["border"])
        if self.props["VALUE"]:
            pyxel.circ(cx, cy, 2, text_color(self))
        ty = y + (self.props["H"] - LINE_H) // 2 + 1
        ui.font.draw(x + BOX + 3, ty, self.props["TEXT"], text_color(self))


@register_widget
class Label(Widget):
    TYPE = "LABEL"
    PROPERTIES = (PropertySpec("TEXT", STR, "LABEL"),
                  PropertySpec("COLOR", INT, COLORS["window_fg"], tuple(range(16))))
    DEFAULT_SIZE = (60, 13)

    def draw(self, ui, x, y, focused):
        color = self.props["COLOR"] if self.enabled else COLORS["disabled_fg"]
        pyxel.clip(x, y, self.props["W"], self.props["H"])
        ui.font.draw(x, y + 1, self.props["TEXT"], color)
        pyxel.clip()


class TextEditing(Widget):
    """Caret movement and editing shared by the text field and the text area.

    The text is kept as lines; the text field has only one.
    """

    FOCUSABLE = True
    MULTI_LINE = False

    def __init__(self, name):
        super().__init__(name)
        self.caret = (0, 0)             # (line, column)
        self.scroll_x = 0               # dots
        self.scroll_y = 0               # lines
        self.blink_start = 0

    @property
    def lines(self):
        return self.props["TEXT"].split("\n")

    def changed(self, name):
        if name == "TEXT":
            lines = self.lines
            line = min(self.caret[0], len(lines) - 1)
            self.caret = (line, min(self.caret[1], len(lines[line])))

    def _set_text(self, lines, caret):
        self.props["TEXT"] = "\n".join(lines)
        self.caret = caret
        self.fire("CHANGE")

    def insert(self, text):
        if self.props["READONLY"]:
            return
        lines = self.lines
        line, col = self.caret
        maxlen = self.props.get("MAXLEN", 0)
        if maxlen:
            text = text[:max(0, maxlen - len(self.props["TEXT"]))]
        if not text:
            return
        current = lines[line]
        new = (current[:col] + text + current[col:]).split("\n")
        lines[line:line + 1] = new
        last = len(new) - 1
        self._set_text(lines, (line + last, len(new[-1]) - (len(current) - col)))

    def delete_back(self):
        line, col = self.caret
        if self.props["READONLY"] or (line == 0 and col == 0):
            return
        lines = self.lines
        if col > 0:
            lines[line] = lines[line][:col - 1] + lines[line][col:]
            self._set_text(lines, (line, col - 1))
        else:
            prev = len(lines[line - 1])
            lines[line - 1:line + 1] = [lines[line - 1] + lines[line]]
            self._set_text(lines, (line - 1, prev))

    def delete_forward(self):
        lines = self.lines
        line, col = self.caret
        if self.props["READONLY"] or (line == len(lines) - 1 and col == len(lines[line])):
            return
        if col < len(lines[line]):
            lines[line] = lines[line][:col] + lines[line][col + 1:]
        else:
            lines[line:line + 2] = [lines[line] + lines[line + 1]]
        self._set_text(lines, (line, col))

    def move(self, key):
        lines = self.lines
        line, col = self.caret
        if key == "left":
            line, col = (line, col - 1) if col > 0 else ((line - 1, len(lines[line - 1])) if line else (0, 0))
        elif key == "right":
            if col < len(lines[line]):
                col += 1
            elif line < len(lines) - 1:
                line, col = line + 1, 0
        elif key == "home":
            col = 0
        elif key == "end":
            col = len(lines[line])
        elif key == "up" and line > 0:
            line, col = line - 1, min(col, len(lines[line - 1]))
        elif key == "down" and line < len(lines) - 1:
            line, col = line + 1, min(col, len(lines[line + 1]))
        else:
            return False
        self.caret = (line, col)
        return True

    def key(self, ev):
        if ev.type == "text":
            self.insert(ev.text)
            return True
        if ev.type != "key" or ev.ctrl or ev.alt:
            return False
        if ev.key == "backspace":
            self.delete_back()
        elif ev.key == "delete":
            self.delete_forward()
        elif ev.key == "enter":
            if self.MULTI_LINE:
                self.insert("\n")
            else:
                self.fire("ENTER")
        elif not self.move(ev.key):
            return False
        return True

    def caret_at(self, font, x, y):
        """Line and column under the point (x, y) inside the widget."""
        lines = self.lines
        line = min(max(0, (y - INNER_PAD) // LINE_H + self.scroll_y), len(lines) - 1)
        target = x - INNER_PAD + self.scroll_x
        text = lines[line]
        col = 0
        while col < len(text) and font.width(text[:col + 1]) - font.char_width(text[col]) // 2 <= target:
            col += 1
        return line, col

    def mouse_down(self, x, y):
        ui = self.window.ui
        self.caret = self.caret_at(ui.font, x - self.props["X"], y - self.props["Y"])
        self.blink_start = ui.frame
        return False

    def draw(self, ui, x, y, focused):
        font = ui.font
        w, h = self.props["W"], self.props["H"]
        pyxel.rect(x, y, w, h, COLORS["field_bg"])
        pyxel.rectb(x, y, w, h, COLORS["focus"] if focused else COLORS["border"])
        lines = self.lines
        line, col = self.caret
        rows = max(1, (h - 2 * INNER_PAD + 2) // LINE_H) if self.MULTI_LINE else 1
        inner_w = w - 2 * INNER_PAD
        caret_x = font.width(lines[line][:col])
        self.scroll_x = min(max(self.scroll_x, caret_x - inner_w + 1), caret_x)
        self.scroll_y = min(max(self.scroll_y, line - rows + 1), line)
        top = y + INNER_PAD if self.MULTI_LINE else y + (h - LINE_H) // 2 + 1
        pyxel.clip(x + 1, y + 1, w - 2, h - 2)
        for i in range(rows):
            n = self.scroll_y + i
            if n < len(lines):
                font.draw(x + INNER_PAD - self.scroll_x, top + i * LINE_H, lines[n], text_color(self))
        if focused and ((ui.frame - self.blink_start) // BLINK_FRAMES) % 2 == 0:
            cy = top + (line - self.scroll_y) * LINE_H - 1
            pyxel.rect(x + INNER_PAD - self.scroll_x + caret_x, cy, 1, LINE_H, COLORS["field_fg"])
        pyxel.clip()


@register_widget
class TextField(TextEditing):
    TYPE = "TEXTFIELD"
    PROPERTIES = (PropertySpec("TEXT", STR, ""), PropertySpec("MAXLEN", INT, 0),
                  PropertySpec("READONLY", INT, 0, (0, 1)))
    EVENTS = ("CHANGE", "ENTER")
    DEFAULT_SIZE = (80, 15)

    def insert(self, text):
        super().insert(text.replace("\n", " "))


@register_widget
class TextArea(TextEditing):
    """Several lines; the text uses CHR$(10) between lines."""

    TYPE = "TEXTAREA"
    PROPERTIES = (PropertySpec("TEXT", STR, ""), PropertySpec("READONLY", INT, 0, (0, 1)))
    EVENTS = ("CHANGE",)
    DEFAULT_SIZE = (100, 45)
    MULTI_LINE = True
