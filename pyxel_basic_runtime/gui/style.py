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
}

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


def mouse_cursor(x, y):
    draw_pattern(x, y, ARROW_CURSOR, {"1": COLORS["cursor_outline"], "2": COLORS["cursor_fg"]})
