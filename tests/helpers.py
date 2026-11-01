"""Drive a BasicScreen with synthetic input."""

from pyxel_basic_runtime import PROGRAM, BasicScreen, Event


def make_screen(source="", mode=PROGRAM, **kwargs):
    return BasicScreen(mode, source, **kwargs)


def run_frames(screen, n=50):
    for _ in range(n):
        screen.step()
        screen.draw()


def text(s):
    return Event("text", text=s)


def key(name):
    return Event("key", key=name)


def type_line(screen, line):
    screen.handle_events([text(line), key("enter")])
    run_frames(screen, 2)
