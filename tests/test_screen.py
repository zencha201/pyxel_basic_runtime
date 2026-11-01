"""The BASIC screen: program end, INPUT, errors, direct mode, stop and resume (DESIGN.md 2 - 4)."""

import pyxel
from helpers import key, make_screen, run_frames, text, type_line

from basic import DIRECT, ENDED, ERROR, STOPPED


def finish(screen):
    """Answer PRESS ANY KEY and return the result."""
    screen.handle_events([key("enter")])
    screen.close()
    return screen.result


def test_program_runs_and_waits_for_a_key():
    screen = make_screen('PRINT 1+2\nPRINT "HELLO"')
    run_frames(screen)
    assert screen.terminal.text() == "3\nHELLO\nOK - PRESS ANY KEY"
    assert screen.result is None
    assert finish(screen).kind == ENDED


def test_inline_input():
    screen = make_screen("INPUT NAME$\nPRINT NAME$")
    run_frames(screen, 2)
    assert screen.typing
    screen.handle_events([text("DAISUKE"), key("enter")])
    run_frames(screen, 2)
    assert screen.terminal.text() == "? DAISUKE\nDAISUKE\nOK - PRESS ANY KEY"


def test_errors_report_the_line():
    screen = make_screen("PRINT 1\nPRINT 2\nPRINT 1/0")
    run_frames(screen)
    assert "?DIVISION BY ZERO IN 3" in screen.terminal.text()
    result = finish(screen)
    assert (result.kind, result.line) == (ERROR, 3) and result.message.startswith("?DIVISION BY ZERO")
    screen = make_screen("PRINT 1\nIF 1\n")
    assert "?IF WITHOUT ENDIF IN 2" in screen.terminal.text()


def test_stop():
    screen = make_screen("*L\nGOTO L")
    run_frames(screen, 3)
    screen.stop()
    assert screen.result.kind == STOPPED


def test_direct_mode():
    screen = make_screen(mode=DIRECT)
    assert screen.terminal.text() == "READY."
    type_line(screen, "PRINT 1+2")
    type_line(screen, 'A$="X"')
    screen.handle_events([key("up"), key("enter")])         # history
    run_frames(screen, 2)
    assert screen.terminal.text() == 'READY.\nPRINT 1+2\n3\nREADY.\nA$="X"\nREADY.\nA$="X"\nREADY.'
    type_line(screen, "exit")
    assert screen.result.kind == "exited"


def test_direct_mode_resume_keeps_the_session():
    screen = make_screen(mode=DIRECT)
    type_line(screen, "A=42")
    screen.handle_events([text("PRINT A")])
    screen.stop()
    screen.close()
    screen.resume(20000, 1000)
    assert screen.result is None and screen.line_editor.text == "PRINT A"
    screen.handle_events([key("enter")])
    run_frames(screen, 2)
    assert screen.terminal.text().endswith("PRINT A\n42\nREADY.")
    # a line stopped while running is abandoned
    type_line(screen, "*L:GOTO L")
    screen.stop()
    screen.close()
    screen.resume(20000, 1000)
    assert screen.terminal.text().endswith("BREAK\nREADY.") and screen.typing
    screen.close()


def test_palette_is_restored_by_close():
    before = list(pyxel.colors)
    screen = make_screen("PRINT 1")
    pyxel.colors[0] = 0x123456          # as if LOAD brought another palette
    screen.close()
    assert list(pyxel.colors) == before


def test_font_and_input_can_be_given():
    calls = []

    class Recorder:
        def poll(self):
            calls.append(1)
            return []

    screen = make_screen("PRINT 1", input=Recorder())
    screen.update()
    assert calls == [1]
    screen.close()
