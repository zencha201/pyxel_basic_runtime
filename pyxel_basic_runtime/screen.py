"""The BASIC screen: runs a program or direct mode on a full-screen terminal (DESIGN.md 2 / 3).

Each frame: read input (stop keys, line editing), run the program for a
limited number of instructions, then draw the graphic plane and the text.
"""

import os
import time
from collections import deque
from dataclasses import dataclass
from typing import Optional

import pyxel
from py_basic_core import (BasicSyntaxError, ReplSession, Runtime, RunState, install_http,
                           install_standard)
from py_basic_core.terminal import LineEditor, TerminalBuffer

from . import commands, functions
from .font import CHAR_W, LINE_H, Font
from .graphics import GraphicsPlane
from .gui import DESIGN_FUNCTION, GuiManager
from .gui import commands as gui_commands
from .gui.style import mouse_cursor
from .host import PyxelHost
from .input import Input

PROGRAM = "program"
DIRECT = "direct"

BG = 0                      # black (DESIGN.md 2)
FG = 7                      # white
BLINK_FRAMES = 30
CHUNK_STEPS = 2000          # instructions between time checks
FRAME_TIME_LIMIT = 0.012    # seconds of BASIC per frame at most
STOP_KEYS = (pyxel.KEY_F5, pyxel.KEY_F6)
END_MESSAGE = "OK - PRESS ANY KEY"
ERROR_PROMPT = "PRESS ANY KEY"
BREAK_MESSAGE = "BREAK"     # a direct-mode line stopped with F5 / F6, shown on resume

# How the screen ended, for the program that shows it (BasicScreen.result.kind).
ENDED = "ended"
ERROR = "error"
STOPPED = "stopped"
EXITED = "exited"


_default_font = None


def default_font():
    """One Font for all screens (loading the BDF file takes a moment)."""
    global _default_font
    if _default_font is None:
        _default_font = Font()
    return _default_font


@dataclass
class BasicResult:
    kind: str
    message: str = ""
    line: Optional[int] = None


class BasicScreen:
    def __init__(self, mode, source="", steps_per_frame=20000, max_call_depth=1000, base_dir=None,
                 font=None, input=None):
        """base_dir: folder that LOAD resolves relative file names against.
        font / input: objects with the interface of font.Font / input.Input; by default
        the font in this package's assets and the keyboard of Pyxel are used.
        """
        self.mode = mode
        self.font = font or default_font()
        self.input = input or Input()
        self.base_dir = base_dir or os.getcwd()
        self._editor_palette = list(pyxel.colors)  # LOAD may bring a palette; restored by close()
        self._own_palette = None                   # the BASIC palette kept while suspended
        self.mouse_visible = False                 # MOUSE command; the editor draws its own cursor
        self.steps_per_frame = steps_per_frame
        self._create_planes()
        self.runtime = Runtime(PyxelHost(self.terminal), max_call_depth)
        install_standard(self.runtime)
        install_http(self.runtime)              # always on (COMMANDS.md 5)
        commands.install(self.runtime, self)
        functions.install(self.runtime, self)
        self.gui = GuiManager(self.font)
        gui_commands.install(self.runtime, self.gui)
        self.line_editor = LineEditor()
        self.keys = deque()         # typed characters for INKEY$()
        self.result = None          # BasicResult once the screen is done
        self._pending_result = None  # shown after "PRESS ANY KEY"
        self._frame = 0
        self.repl = None
        if mode == DIRECT:
            self.repl = ReplSession(self.runtime)
            self.repl.start()
            self.phase = "line"     # waiting for a direct-mode line
        else:
            self.phase = "run"
            try:
                self.runtime.load(source)
            except BasicSyntaxError as e:
                self._show_error(e)
            else:
                # The GUI design made by the designer runs before the main program.
                self.runtime.call_event(DESIGN_FUNCTION)

    def _create_planes(self):
        self.terminal = TerminalBuffer(pyxel.width // CHAR_W, pyxel.height // LINE_H,
                                       self._cell_width)
        self.graphics = GraphicsPlane(pyxel.width, pyxel.height, self.font)

    def _cell_width(self, ch):
        return 2 if self.font.char_width(ch) > CHAR_W else 1

    # --- state -----------------------------------------------------------------
    @property
    def typing(self):
        """True while a line is being typed (direct mode prompt or INPUT)."""
        if self.phase == "line":
            return True
        return self.phase == "run" and self.runtime.state == RunState.WAITING_INPUT

    def pop_key(self):
        return self.keys.popleft() if self.keys else ""

    def set_mouse_visible(self, visible):
        self.mouse_visible = visible
        pyxel.mouse(visible)

    def close(self):
        """Undo changes that would leak into the editor screen."""
        self._own_palette = list(pyxel.colors)
        pyxel.colors[:] = self._editor_palette
        pyxel.mouse(False)

    def resume(self, steps_per_frame, max_call_depth, base_dir=None):
        """Show a suspended direct-mode session again (DESIGN.md 4).

        Variables, history, the typed line and the graphics are kept. A line
        that was stopped while running is abandoned and READY. is shown.
        """
        self._editor_palette = list(pyxel.colors)
        if self._own_palette is not None:
            pyxel.colors[:] = self._own_palette
        pyxel.mouse(self.mouse_visible)
        self.steps_per_frame = steps_per_frame
        self.runtime.max_call_depth = max_call_depth
        self.base_dir = base_dir or self.base_dir
        self.result = None
        self.keys.clear()
        if (self.graphics.width, self.graphics.height) != (pyxel.width, pyxel.height):
            self._create_planes()       # the screen size changed in the editor
            self.runtime.host.terminal = self.terminal
            self.line_editor.clear()
            self.repl.start()
        elif self.phase != "line":
            self.line_editor.clear()    # a half-typed INPUT answer belongs to the stopped line
            self._new_line()
            self.terminal.write(BREAK_MESSAGE + "\n")
            self.repl.start()
        self.phase = "line"
        self.terminal.make_room(self.line_editor.text)

    def stop(self):
        """F5 / F6: stop at once and go back to the editor."""
        self.runtime.stop()
        self.result = BasicResult(STOPPED)

    # --- per frame -------------------------------------------------------------
    def update(self):
        events = self.input.poll()
        if any(pyxel.btnp(k) for k in STOP_KEYS):
            self.stop()
            return
        self.handle_events(events)
        self.step()

    def handle_events(self, events):
        for ev in events:
            if self.result is not None:
                return
            if ev.type == "key" and ev.key in ("f5", "f6"):
                continue            # stopping is checked with btnp (no key repeat)
            if self.phase == "any_key":
                if ev.type in ("key", "text") or ev.type == "mouse_down":
                    self.result = self._pending_result
                continue
            if self.gui.handle(ev):
                continue
            if self.typing:
                self._edit_line(ev)
            elif ev.type == "text":
                self.keys.extend(ev.text)
            elif ev.type == "key" and ev.key in ("enter", "backspace"):
                self.keys.append("\r" if ev.key == "enter" else "\b")

    def _edit_line(self, ev):
        ed = self.line_editor
        if ev.type == "text":
            ed.insert(ev.text)
        elif ev.type == "key" and not ev.ctrl and not ev.alt:
            action = {
                "backspace": ed.backspace, "delete": ed.delete,
                "left": ed.left, "right": ed.right, "home": ed.home, "end": ed.end,
            }.get(ev.key)
            if action is not None:
                action()
            elif ev.key == "up" and self.phase == "line":
                ed.history_prev()
            elif ev.key == "down" and self.phase == "line":
                ed.history_next()
            elif ev.key == "enter":
                self._submit_line()
                return
        self.terminal.make_room(ed.text)

    def _submit_line(self):
        line = self.line_editor.submit(remember=self.phase == "line")
        self.terminal.write(line + "\n")
        if self.phase == "line":
            if self.repl.submit(line):
                self.phase = "run"
        else:
            self.runtime.provide_input(line)
            self._after_run(self.runtime.state)

    def step(self):
        """Run the program for one frame."""
        self._frame += 1
        self.gui.update()
        if self.result is not None or self.phase != "run":
            return
        rt = self.runtime
        self._start_gui_event()
        if rt.state not in (RunState.RUNNING, RunState.WAITING_FRAMES):
            if rt.state == RunState.FINISHED:
                self._after_run(rt.state)      # a GUI program ends when its windows are closed
            return
        deadline = time.perf_counter() + FRAME_TIME_LIMIT
        remaining = self.steps_per_frame
        state = rt.run(min(CHUNK_STEPS, remaining))
        remaining -= CHUNK_STEPS
        while state == RunState.RUNNING and remaining > 0 and time.perf_counter() < deadline:
            state = rt.run(min(CHUNK_STEPS, remaining))
            remaining -= CHUNK_STEPS
        self._after_run(state)

    def _start_gui_event(self):
        """Call the BASIC handler of a GUI event when the program is idle (GUI.md 5)."""
        rt = self.runtime
        if rt.in_event or not self.gui.pending:
            return
        if rt.state not in (RunState.WAITING_FRAMES, RunState.FINISHED):
            return                              # the program is busy: the event waits
        rt.call_event(self.gui.next_handler())

    def _waiting_for_gui(self):
        rt = self.runtime
        return (not rt.ended_by_end
                and (rt.in_event or self.gui.pending or self.gui.has_visible_windows()))

    def _after_run(self, state):
        if state == RunState.EXITED:
            self.result = BasicResult(EXITED)
        elif state not in (RunState.FINISHED, RunState.ERROR):
            return
        elif self.mode == DIRECT:
            self.repl.finish()
            self.phase = "line"
        elif state == RunState.FINISHED and self._waiting_for_gui():
            return                              # windows are open: wait for events
        elif state == RunState.FINISHED and self.gui.used and not self.runtime.ended_by_end:
            self.result = BasicResult(ENDED)    # the last window was closed
        elif state == RunState.FINISHED:
            self._new_line()
            self.terminal.write(END_MESSAGE)
            self._wait_key(BasicResult(ENDED))
        else:
            self._show_error(self.runtime.error)

    def _show_error(self, error):
        self._new_line()
        self.terminal.write(error.message() + "\n" + ERROR_PROMPT)
        self._wait_key(BasicResult(ERROR, error.message(), error.line))

    def _new_line(self):
        if self.terminal.col != 0:
            self.terminal.write("\n")

    def _wait_key(self, result):
        self._pending_result = result
        self.phase = "any_key"

    # --- drawing ---------------------------------------------------------------
    def draw(self):
        pyxel.cls(BG)
        self.graphics.draw()
        font = self.font
        term = self.terminal
        for r in range(term.rows):
            text = term.row_text(r)
            if text.strip():
                font.draw(0, r * LINE_H, text, FG)
        if self.typing:
            self._draw_line_editor()
        elif self.phase == "any_key":
            self._draw_caret(term.row, term.col, "")
        self.gui.draw()
        if self.gui.has_visible_windows() and not self.mouse_visible:
            mouse_cursor(pyxel.mouse_x, pyxel.mouse_y)

    def _draw_line_editor(self):
        ed = self.line_editor
        places, end = self.terminal.layout(ed.text)
        for ch, (row, col) in zip(ed.text, places):
            self.font.draw(col * CHAR_W, row * LINE_H, ch, FG)
        if ed.cursor < len(places):
            row, col = places[ed.cursor]
            self._draw_caret(row, col, ed.text[ed.cursor])
        else:
            self._draw_caret(end[0], end[1], "")

    def _draw_caret(self, row, col, under):
        if (self._frame // BLINK_FRAMES) % 2:
            return
        if col >= self.terminal.cols:
            row, col = row + 1, 0
        x, y = col * CHAR_W, row * LINE_H
        w = self.font.width(under) if under else CHAR_W
        pyxel.rect(x, y, w, LINE_H, FG)
        if under:
            self.font.draw(x, y, under, BG)
