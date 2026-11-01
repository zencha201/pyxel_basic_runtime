"""The bitmap font of the BASIC screen (umplus_j12r.bdf, DESIGN.md 6)."""

import os
import unicodedata

import pyxel

FONT_FILE = "umplus_j12r.bdf"
CHAR_W = 6          # width of a half-width character
LINE_H = 13         # height of a text line

# Shown in place of characters the font does not contain.
MISSING_NARROW = "?"
MISSING_WIDE = "〓"


def default_font_path():
    """The font in this package's assets, or the copy in the Pyxel package."""
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", FONT_FILE),
        os.path.join(os.path.dirname(pyxel.__file__), "examples", "assets", FONT_FILE),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    raise FileNotFoundError(FONT_FILE)


class Font:
    """Text measurement and drawing. Call after pyxel.init()."""

    def __init__(self, path=None):
        self.font = pyxel.Font(path or default_font_path())
        self._widths = {}
        self._subst = {}

    def _probe(self, ch):
        w = self.font.text_width(ch)
        if w > 0:
            self._widths[ch] = w
            return
        # Use a compatible glyph when one exists (e.g. half-width kana -> full-width kana).
        sub = unicodedata.normalize("NFKC", ch)
        if len(sub) != 1 or sub == ch or self.font.text_width(sub) == 0:
            wide = unicodedata.east_asian_width(ch) in ("W", "F")
            sub = MISSING_WIDE if wide else MISSING_NARROW
        self._subst[ch] = sub
        self._widths[ch] = self.font.text_width(sub)

    def char_width(self, ch):
        w = self._widths.get(ch)
        if w is None:
            self._probe(ch)
            w = self._widths[ch]
        return w

    def width(self, s):
        return sum(self.char_width(ch) for ch in s)

    def displayable(self, s):
        """Replace characters missing from the font with placeholders."""
        for ch in s:
            if ch not in self._widths:
                self._probe(ch)
        if not self._subst:
            return s
        return "".join(self._subst.get(ch, ch) for ch in s)

    def draw(self, x, y, s, col):
        if s:
            pyxel.text(x, y, self.displayable(s), col, self.font)
