"""Look of the GUI: the colors and sizes of the editor's dialogs (GUI.md 6).

The values follow the editor's UI guideline (standard theme), so windows made
with BASIC look like the editor's own windows.
"""

import pyxel

from ..font import LINE_H

BAR_H = LINE_H + 1          # title bar
PAD = 2
SHADOW = 2
BOX = 9                     # check box / radio button

COLORS = {
    "window_bg": 7, "window_fg": 0,
    "title_bg": 1, "title_fg": 7, "title_inactive_bg": 13,
    "border": 0, "shadow": 0, "focus": 8,
    "field_bg": 7, "field_fg": 0,
    "select_bg": 12, "select_fg": 0,
    "disabled_fg": 13,
    "cursor_fg": 7, "cursor_outline": 0,
    "scroll_track": 1, "scroll_thumb": 6,
    "list_sel_bg": 1, "list_sel_fg": 7,
}

SCROLLBAR_W = 7             # thickness of a scroll bar (and the size of its arrow buttons)
KEY_HOLD = 20               # frames before a held scroll button repeats
KEY_REPEAT = 3              # frames between repeats

CHECK = [
    "......1",
    ".....11",
    "1...11.",
    "11.11..",
    ".111...",
    "..1....",
]

ARROW_CURSOR = [
    "1.........",
    "11........",
    "121.......",
    "1221......",
    "12221.....",
    "122221....",
    "1222221...",
    "12222221..",
    "122221111.",
    "1221221...",
    "121.1221..",
    "11..1221..",
    "....1221..",
    ".....11...",
]


def draw_pattern(x, y, pattern, colors):
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            c = colors.get(ch)
            if c is not None:
                pyxel.pset(x + i, y + j, c)


def check_mark(x, y, col):
    draw_pattern(x, y, CHECK, {"1": col})


def triangle(x, y, direction, col):
    """A 5 x 3 (or 3 x 5) arrow pointing "up", "down", "left" or "right"; (x, y) is its top-left."""
    if direction == "up":
        pyxel.tri(x + 2, y, x, y + 2, x + 4, y + 2, col)
    elif direction == "down":
        pyxel.tri(x + 2, y + 2, x, y, x + 4, y, col)
    elif direction == "left":
        pyxel.tri(x, y + 2, x + 2, y, x + 2, y + 4, col)
    else:
        pyxel.tri(x + 2, y + 2, x, y, x, y + 4, col)


def mouse_cursor(x, y):
    draw_pattern(x, y, ARROW_CURSOR, {"1": COLORS["cursor_outline"], "2": COLORS["cursor_fg"]})
