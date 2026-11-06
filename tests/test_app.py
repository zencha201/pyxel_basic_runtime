"""Running BASIC on its own (DESIGN.md 7)."""

import os
import subprocess
import sys

from helpers import key, run_frames, type_line

from retro_basic_runtime import DIRECT, PROGRAM
from retro_basic_runtime.app import program_path, read_source

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_program_path():
    assert program_path(["main.py"]) is None
    assert program_path(["main.py", "game.bas"]) == "game.bas"
    assert program_path(["main.py", "-x", "game.bas"]) == "game.bas"
    assert program_path(["pyxel", "play", "retro_basic_runtime.pyxapp"]) is None


def test_read_source_encodings(tmp_path):
    p = tmp_path / "a.bas"
    p.write_bytes('﻿PRINT "日本"'.encode("utf-8"))
    assert read_source(str(p)) == 'PRINT "日本"'
    p.write_bytes('PRINT "日本"'.encode("cp932"))
    assert read_source(str(p)) == 'PRINT "日本"'


def test_file_runs_and_the_app_ends(basic_app, tmp_path):
    p = tmp_path / "hello.bas"
    p.write_text('PRINT "HI"', encoding="utf-8")
    screen = basic_app.start(str(p))
    assert screen.mode == PROGRAM and screen.base_dir == str(tmp_path)
    run_frames(screen, 2)
    quits = basic_app.quit.count
    screen.handle_events([key("enter")])        # PRESS ANY KEY
    basic_app.update()
    assert basic_app.quit.count == quits + 1


def test_direct_mode_without_a_file(basic_app):
    screen = basic_app.start(None)
    assert screen.mode == DIRECT
    quits = basic_app.quit.count
    type_line(screen, "EXIT")
    basic_app.update()
    assert basic_app.quit.count == quits + 1


def test_missing_file_is_reported():
    result = subprocess.run([sys.executable, os.path.join(REPO_DIR, "main.py"), "no_such.bas"],
                            capture_output=True, text=True, timeout=60)
    assert result.returncode == 1 and "File not found: no_such.bas" in result.stderr
