"""Drawing and resource commands of the Pyxel version (COMMANDS.md 2)."""

import os

import pyxel

from .core import WaitFrames
from .core.errors import FILE_NOT_FOUND, ILLEGAL_FUNCTION_CALL

PALETTE_SIZE = 16
HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def color_arg(ctx, value):
    c = ctx.expect_int(value)
    if not 0 <= c < PALETTE_SIZE:
        raise ctx.error(ILLEGAL_FUNCTION_CALL, "color %d" % c)
    return c


def int_args(ctx, args, count):
    """The first ``count`` arguments as integers and the last one as a color."""
    values = [ctx.expect_int(v) for v in args[:count]]
    return values, color_arg(ctx, args[count])


def install(runtime, screen):
    """Register the commands; ``screen`` is the BasicScreen that owns the planes."""

    def cls(ctx, args):
        screen.graphics.clear(color_arg(ctx, args[0]) if args else 0)
        screen.terminal.clear()

    def text(ctx, args):
        x, y = ctx.expect_int(args[0]), ctx.expect_int(args[1])
        s = args[2] if isinstance(args[2], str) else str(ctx.expect_int(args[2]))
        screen.graphics.text(x, y, s, color_arg(ctx, args[3]))

    def line(ctx, args):
        (x1, y1, x2, y2), c = int_args(ctx, args, 4)
        screen.graphics.image.line(x1, y1, x2, y2, c)

    def pset(ctx, args):
        (x, y), c = int_args(ctx, args, 2)
        screen.graphics.image.pset(x, y, c)

    def rect(ctx, args):
        (x, y, w, h), c = int_args(ctx, args, 4)
        screen.graphics.image.rect(x, y, w, h, c)

    def rectb(ctx, args):
        (x, y, w, h), c = int_args(ctx, args, 4)
        screen.graphics.image.rectb(x, y, w, h, c)

    def circ(ctx, args):
        (x, y, r), c = int_args(ctx, args, 3)
        screen.graphics.image.circ(x, y, r, c)

    def circb(ctx, args):
        (x, y, r), c = int_args(ctx, args, 3)
        screen.graphics.image.circb(x, y, r, c)

    def load(ctx, args):
        """LOAD "file.pyxres": image banks, tilemaps and sounds (relative to the program)."""
        name = ctx.expect_str(args[0])
        path = os.path.join(screen.base_dir, name)
        if not os.path.isfile(path):
            raise ctx.error(FILE_NOT_FOUND, name)
        try:
            pyxel.load(path)
        except Exception as e:
            raise ctx.error(ILLEGAL_FUNCTION_CALL, str(e))

    def image_bank(ctx, value):
        bank = ctx.expect_int(value)
        if not 0 <= bank < len(pyxel.images):
            raise ctx.error(ILLEGAL_FUNCTION_CALL, "image bank %d" % bank)
        return pyxel.images[bank]

    def imgset(ctx, args):
        """IMGSET bank,x,y,row$: write one row of pixels; each hex digit is a color."""
        image = image_bank(ctx, args[0])
        x, y = ctx.expect_int(args[1]), ctx.expect_int(args[2])
        row = ctx.expect_str(args[3])
        if not all(ch in HEX_DIGITS for ch in row):
            raise ctx.error(ILLEGAL_FUNCTION_CALL, "not hex: " + row)
        if row:
            image.set(x, y, [row])

    def blt(ctx, args):
        """BLT x,y,bank,u,v,w,h[,colkey]: copy from an image bank (negative w / h flips)."""
        image = image_bank(ctx, args[2])
        x, y, u, v, w, h = (ctx.expect_int(args[i]) for i in (0, 1, 3, 4, 5, 6))
        colkey = color_arg(ctx, args[7]) if len(args) > 7 else None
        screen.graphics.image.blt(x, y, image, u, v, w, h, colkey)

    def mouse(ctx, args):
        """MOUSE 1 / MOUSE 0: show or hide the mouse cursor."""
        screen.set_mouse_visible(ctx.expect_int(args[0]) != 0)

    def wait(ctx, args):
        n = ctx.expect_int(args[0])
        if n < 0:
            raise ctx.error(ILLEGAL_FUNCTION_CALL)
        return WaitFrames(n)

    for name, fn, min_args, max_args in (
        ("CLS", cls, 0, 1),
        ("TEXT", text, 4, 4),
        ("LINE", line, 5, 5),
        ("PSET", pset, 3, 3),
        ("RECT", rect, 5, 5),
        ("RECTB", rectb, 5, 5),
        ("CIRC", circ, 4, 4),
        ("CIRCB", circb, 4, 4),
        ("LOAD", load, 1, 1),
        ("BLT", blt, 7, 8),
        ("IMGSET", imgset, 4, 4),
        ("MOUSE", mouse, 1, 1),
        ("WAIT", wait, 1, 1),
    ):
        runtime.register_command(name, fn, min_args, max_args)
