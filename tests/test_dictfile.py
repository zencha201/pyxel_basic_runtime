"""DWRITE / DREAD from the BASIC screen (COMMANDS.md 6): files are next to the program."""

from helpers import make_screen, run_frames


def test_files_are_relative_to_the_program(tmp_path):
    screen = make_screen('DICT S$\nS$("NAME")="TARO"\nDWRITE "save.json", S$\nERASE S$\n'
                         'DREAD "save.json", S$\nPRINT S$("NAME")', base_dir=str(tmp_path))
    run_frames(screen, 3)
    assert screen.terminal.text().startswith("TARO")
    assert (tmp_path / "save.json").is_file()
    screen.close()
