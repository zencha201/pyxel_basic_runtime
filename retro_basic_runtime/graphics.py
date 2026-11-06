"""Graphic plane: an image the drawing commands paint on, shown under the text."""

import pyxel


class GraphicsPlane:
    def __init__(self, width, height, font=None):
        self.width = width
        self.height = height
        self.font = font            # font.Font (or the same interface) for TEXT
        self.image = pyxel.Image(width, height)
        self.image.cls(0)

    def clear(self, color):
        self.image.cls(color)

    def text(self, x, y, s, color):
        if self.font is None:
            self.image.text(x, y, s, color)
        else:
            self.image.text(x, y, self.font.displayable(s), color, self.font.font)

    def draw(self):
        pyxel.blt(0, 0, self.image, 0, 0, self.width, self.height)
