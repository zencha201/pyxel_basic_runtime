"""Pyxel commands and functions (COMMANDS.md)."""

import pyxel
from helpers import make_screen, run_frames, text


def output(source, frames=3, **kwargs):
    screen = make_screen(source, **kwargs)
    run_frames(screen, frames)
    screen.close()
    return screen.terminal.text()


def test_drawing_commands_and_pget():
    out = output('CLS 1\nPSET 3,4,8\nLINE 0,0,10,0,9\nRECT 20,20,5,5,10\n'
                 'CIRCB 50,50,5,11\nTEXT 0,30,"HI",7\nPRINT PGET(3,4);PGET(5,0);PGET(0,100)')
    assert out.startswith("891")


def test_bad_color_is_an_error():
    assert "?ILLEGAL FUNCTION CALL (color 99) IN 1" in output("CLS 99", 2)


def test_wait_and_inkey():
    screen = make_screen('WAIT 3\n*L\nK$=INKEY$()\nIF K$="" THEN WAIT 1:GOTO L\nPRINT K$')
    run_frames(screen, 5)
    assert screen.terminal.text() == ""
    screen.handle_events([text("Q")])
    run_frames(screen, 3)
    assert screen.terminal.text().startswith("Q")
    screen.close()


def test_load_and_blt(tmp_path):
    pyxel.images[0].cls(0)
    pyxel.images[0].pset(1, 1, 12)
    pyxel.images[0].pset(2, 2, 5)
    pyxel.save(str(tmp_path / "res.pyxres"))
    pyxel.images[0].cls(0)
    out = output('LOAD "res.pyxres"\nBLT 10,10,0,0,0,8,8\nBLT 20,10,0,0,0,-8,8,5\n'
                 'PRINT PGET(11,11);",";PGET(12,12);",";PGET(26,11);",";PGET(25,12)',
                 base_dir=str(tmp_path))
    # flipped copy: (1,1) -> x=20+6; colour 5 is transparent at (2,2) -> x=20+5
    assert out.startswith("12,5,12,0")


def test_load_errors_and_gamepad_names():
    out = output('PRINT BTN("GAMEPAD1_A");BTNP("gamepad4_right")\nLOAD "missing.pyxres"', 2)
    assert out.startswith("00") and "?FILE NOT FOUND (missing.pyxres) IN 2" in out
    assert "?ILLEGAL FUNCTION CALL (image bank 3) IN 1" in output("BLT 0,0,3,0,0,8,8", 2)


def test_imgset_with_data_and_blt():
    out = output('FOR J=0 TO 1:READ R$:IMGSET 1,0,J,R$:NEXT\n'
                 'BLT 10,10,1,0,0,4,2,0\n'
                 'PRINT PGET(10,10);",";PGET(11,10);",";PGET(13,11)\n'
                 'IMGSET 1,0,0,"0G"\n'
                 'DATA "0a7F","000c"')
    assert out.startswith("0,10,12")         # 0 is transparent: background (0) shows
    assert "?ILLEGAL FUNCTION CALL (not hex: 0G) IN 4" in out


def test_mouse_command():
    screen = make_screen("MOUSE 1")
    run_frames(screen, 2)
    assert screen.mouse_visible
    screen.close()


def test_screen_size_functions():
    assert output('PRINT SCREENW();",";SCREENH()', 2).startswith("%d,%d" % (pyxel.width, pyxel.height))
