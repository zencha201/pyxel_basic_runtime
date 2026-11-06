"""BASIC on its own (DESIGN.md 7): run the .bas file given on the command line,
otherwise start direct mode. The application ends when BASIC does.
"""

import os
import sys

import pyxel

from .screen import DIRECT, PROGRAM, BasicScreen

APP_TITLE = "BASIC"
SCREEN_W = 256
SCREEN_H = 240
PYXAPP_EXTENSION = ".pyxapp"
ENCODINGS = ("utf-8-sig", "cp932")     # tried in this order


def program_path(argv):
    """The .bas file named on the command line, or None.

    Under "pyxel play x.pyxapp" argv is left as it is, so the arguments up to
    the package are not program files.
    """
    args = argv[1:]
    for i in range(len(args) - 1, -1, -1):
        if args[i].endswith(PYXAPP_EXTENSION):
            args = args[i + 1:]
            break
    files = [a for a in args if not a.startswith("-")]
    return files[0] if files else None


def read_source(path):
    with open(path, "rb") as fp:
        data = fp.read()
    for encoding in ENCODINGS:
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode(ENCODINGS[0], errors="replace")


class BasicApp:
    def __init__(self, path=None, width=SCREEN_W, height=SCREEN_H, headless=False, quit=None):
        """quit: called when BASIC has ended (pyxel.quit by default; tests pass their own)."""
        kwargs = dict(title=APP_TITLE, quit_key=pyxel.KEY_NONE)
        if headless:
            kwargs["headless"] = True
        cwd = os.getcwd()
        pyxel.init(width, height, **kwargs)
        os.chdir(cwd)       # pyxel.init() moves to the script's folder; keep the user's one
        pyxel.integer_scale(True)
        self.quit = quit or pyxel.quit
        self.screen = self.start(path)

    def start(self, path=None):
        """A screen running ``path``, or direct mode when it is None."""
        if path is None:
            self.screen = BasicScreen(DIRECT)
        else:
            base_dir = os.path.dirname(os.path.abspath(path))
            self.screen = BasicScreen(PROGRAM, read_source(path), base_dir=base_dir)
        return self.screen

    def update(self):
        if self.screen.result is None:
            self.screen.update()
        if self.screen.result is not None:
            self.screen.close()
            self.quit()

    def draw(self):
        self.screen.draw()

    def run(self):
        pyxel.run(self.update, self.draw)


def main(argv=None):
    path = program_path(sys.argv if argv is None else argv)
    if path is not None and not os.path.isfile(path):
        print("File not found: " + path, file=sys.stderr)
        return 1
    BasicApp(path).run()
    return 0
