"""Keyboard and mouse input of the BASIC screen as a per-frame list of events.

Only what the BASIC screen needs: editing keys (with key repeat), F5 / F6,
typed text and mouse clicks. Tests feed Event objects directly.
"""

from dataclasses import dataclass

import pyxel

KEY_HOLD = 20       # frames before key repeat starts
KEY_REPEAT = 3      # frames between repeats

KEYS = {
    "left": pyxel.KEY_LEFT, "right": pyxel.KEY_RIGHT, "up": pyxel.KEY_UP, "down": pyxel.KEY_DOWN,
    "home": pyxel.KEY_HOME, "end": pyxel.KEY_END,
    "backspace": pyxel.KEY_BACKSPACE, "delete": pyxel.KEY_DELETE,
    "enter": pyxel.KEY_RETURN, "kp_enter": pyxel.KEY_KP_ENTER,
    "escape": pyxel.KEY_ESCAPE, "tab": pyxel.KEY_TAB,
    "f5": pyxel.KEY_F5, "f6": pyxel.KEY_F6,
}


@dataclass
class Event:
    type: str                   # "key", "text" or "mouse_down"
    key: str = ""               # a name of KEYS for "key" ("kp_enter" is reported as "enter")
    text: str = ""
    ctrl: bool = False
    alt: bool = False


class Input:
    def poll(self):
        """Events of this frame."""
        ctrl = pyxel.btn(pyxel.KEY_CTRL) or pyxel.btn(pyxel.KEY_GUI)
        alt = pyxel.btn(pyxel.KEY_ALT)
        events = []
        if pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT) or pyxel.btnp(pyxel.MOUSE_BUTTON_RIGHT):
            events.append(Event("mouse_down"))
        for name, code in KEYS.items():
            if pyxel.btnp(code, hold=KEY_HOLD, repeat=KEY_REPEAT):
                key = "enter" if name == "kp_enter" else name
                events.append(Event("key", key=key, ctrl=ctrl, alt=alt))
        text = pyxel.input_text
        if text and not ctrl and not alt:
            text = "".join(ch for ch in text if ch >= " " and ch != "\x7f")
            if text:
                events.append(Event("text", text=text))
        return events
