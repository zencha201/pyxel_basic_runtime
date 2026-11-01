"""Input and screen functions of the Pyxel version (COMMANDS.md 3)."""

import pyxel

from .core.errors import ILLEGAL_FUNCTION_CALL

# Key names accepted by BTN / BTNP (COMMANDS.md appendix).
KEY_CODES = {c: getattr(pyxel, "KEY_" + c) for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"}
KEY_CODES.update({
    "LEFT": pyxel.KEY_LEFT, "RIGHT": pyxel.KEY_RIGHT, "UP": pyxel.KEY_UP, "DOWN": pyxel.KEY_DOWN,
    "SPACE": pyxel.KEY_SPACE, "ENTER": pyxel.KEY_RETURN, "ESC": pyxel.KEY_ESCAPE,
    "TAB": pyxel.KEY_TAB, "BACKSPACE": pyxel.KEY_BACKSPACE,
    "SHIFT": pyxel.KEY_SHIFT, "CTRL": pyxel.KEY_CTRL, "ALT": pyxel.KEY_ALT,
    "MOUSE_LEFT": pyxel.MOUSE_BUTTON_LEFT, "MOUSE_RIGHT": pyxel.MOUSE_BUTTON_RIGHT,
})
# Gamepad buttons: GAMEPAD1_A ... GAMEPAD4_RIGHT (COMMANDS.md appendix).
GAMEPAD_BUTTONS = {
    "A": "A", "B": "B", "X": "X", "Y": "Y",
    "BACK": "BACK", "GUIDE": "GUIDE", "START": "START",
    "LEFTSTICK": "LEFTSTICK", "RIGHTSTICK": "RIGHTSTICK",
    "LEFTSHOULDER": "LEFTSHOULDER", "RIGHTSHOULDER": "RIGHTSHOULDER",
    "UP": "DPAD_UP", "DOWN": "DPAD_DOWN", "LEFT": "DPAD_LEFT", "RIGHT": "DPAD_RIGHT",
}
GAMEPAD_COUNT = 4
for _n in range(1, GAMEPAD_COUNT + 1):
    for _name, _button in GAMEPAD_BUTTONS.items():
        KEY_CODES["GAMEPAD%d_%s" % (_n, _name)] = getattr(pyxel, "GAMEPAD%d_BUTTON_%s" % (_n, _button))


def key_code(ctx, value):
    code = KEY_CODES.get(ctx.expect_str(value).upper())
    if code is None:
        raise ctx.error(ILLEGAL_FUNCTION_CALL, "key " + value)
    return code


def install(runtime, screen):

    def pget(ctx, args):
        x, y = ctx.expect_int(args[0]), ctx.expect_int(args[1])
        if not (0 <= x < screen.graphics.width and 0 <= y < screen.graphics.height):
            return 0
        return screen.graphics.image.pget(x, y)

    def btn(ctx, args):
        return 1 if pyxel.btn(key_code(ctx, args[0])) else 0

    def btnp(ctx, args):
        return 1 if pyxel.btnp(key_code(ctx, args[0])) else 0

    def inkey(ctx, args):
        return screen.pop_key()

    def screen_w(ctx, args):
        return screen.graphics.width

    def screen_h(ctx, args):
        return screen.graphics.height

    def mouse_x(ctx, args):
        return pyxel.mouse_x

    def mouse_y(ctx, args):
        return pyxel.mouse_y

    for name, fn, min_args, max_args in (
        ("PGET", pget, 2, 2),
        ("BTN", btn, 1, 1),
        ("BTNP", btnp, 1, 1),
        ("INKEY$", inkey, 0, 0),
        ("SCREENW", screen_w, 0, 0),
        ("SCREENH", screen_h, 0, 0),
        ("MOUSEX", mouse_x, 0, 0),
        ("MOUSEY", mouse_y, 0, 0),
    ):
        runtime.register_function(name, fn, min_args, max_args)
