"""GUI of BASIC programs: windows, widgets, events (GUI.md)."""

from helpers import key, make_screen, run_frames, text

from pyxel_basic_runtime import ENDED, ERROR, Event
from pyxel_basic_runtime.gui import INT, PropertySpec, Widget, register_widget, widget_types
from pyxel_basic_runtime.gui.style import BAR_H

DESIGN = """
FUNCTION GUI_DESIGN()
    WINDOW "MAIN", "TEST", 10, 20, 150, 100
    WIDGET "MAIN", "BUTTON", "OK", 5, 5, 40, 16
    WIDGET "MAIN", "LABEL", "MSG", 5, 25, 100, 13
    WIDGET "MAIN", "TEXTFIELD", "NAME", 5, 40, 80, 15
    WIDGET "MAIN", "CHECKBOX", "CHK", 5, 60, 60, 15
    WIDGET "MAIN", "RADIO", "R1", 70, 60, 40, 15
    WIDGET "MAIN", "RADIO", "R2", 70, 78, 40, 15
    PROPERTY "OK", "TEXT", "OK"
    PROPERTY "R1", "VALUE", 1
    HANDLER "OK", "CLICK", "OK_CLICK"
    HANDLER "NAME", "ENTER", "OK_CLICK"
    HANDLER "CHK", "CHANGE", "CHK_CHANGE"
    HANDLER "MAIN", "CLOSE", "MAIN_CLOSE"
END FUNCTION
"""

HANDLERS = """
FUNCTION OK_CLICK()
    GLOBAL CLICKS
    CLICKS=CLICKS+1
    SETPROP "MSG", "TEXT", "HELLO " + GETPROP$("NAME", "TEXT")
END FUNCTION
FUNCTION CHK_CHANGE()
    PRINT "CHK";GETPROP("CHK", "VALUE")
END FUNCTION
FUNCTION MAIN_CLOSE()
    PRINT "CLOSED"
END FUNCTION
"""


def client(screen, window, x, y):
    """Screen position of client point (x, y) of a window."""
    w = screen.gui.windows[window]
    return w.props["X"] + 1 + x, w.props["Y"] + BAR_H + y


def click(screen, x, y):
    screen.handle_events([Event("mouse_down", x=x, y=y), Event("mouse_up", x=x, y=y)])
    run_frames(screen, 3)


def start(main='SHOW "MAIN"'):
    screen = make_screen(main + "\n" + HANDLERS + DESIGN)
    run_frames(screen, 3)
    return screen


def prop(screen, name, p):
    return screen.gui.find(name).get(p)


def test_design_runs_first_and_events_call_handlers():
    screen = start()
    assert screen.gui.has_visible_windows() and screen.result is None
    screen.handle_events([Event("mouse_down", x=0, y=0)])         # outside the window: ignored
    click(screen, *client(screen, "MAIN", 50, 47))                 # the text field gets the focus
    screen.handle_events([text("TARO")])
    click(screen, *client(screen, "MAIN", 10, 10))                 # OK button
    assert prop(screen, "MSG", "TEXT") == "HELLO TARO"
    screen.handle_events([key("tab"), key("enter")])               # focus OK -> NAME, ENTER there
    run_frames(screen, 3)
    assert screen.runtime.globals.values["CLICKS"] == 2
    screen.close()


def test_check_box_and_radio_buttons():
    screen = start()
    click(screen, *client(screen, "MAIN", 8, 66))
    assert prop(screen, "CHK", "VALUE") == 1 and screen.terminal.text().startswith("CHK1")
    click(screen, *client(screen, "MAIN", 75, 84))                 # R2
    assert (prop(screen, "R1", "VALUE"), prop(screen, "R2", "VALUE")) == (0, 1)
    screen.close()


def test_closing_the_last_window_ends_the_program():
    screen = start()
    w = screen.gui.windows["MAIN"]
    x, y, fw, _ = w.frame_rect
    click(screen, x + fw - 5, y + 5)                                # close box
    run_frames(screen, 2)
    assert "CLOSED" in screen.terminal.text()
    assert screen.result is not None and screen.result.kind == ENDED
    screen.close()


def test_end_in_a_handler_ends_with_the_usual_message():
    screen = make_screen('SHOW "MAIN"\n' + HANDLERS + DESIGN.replace('"OK_CLICK"\n    HANDLER "NAME"',
                         '"QUIT"\n    HANDLER "NAME"') + "FUNCTION QUIT()\nEND\nEND FUNCTION")
    run_frames(screen, 3)
    click(screen, *client(screen, "MAIN", 10, 10))
    run_frames(screen, 2)
    assert screen.terminal.text().endswith("OK - PRESS ANY KEY")
    screen.close()


def test_events_run_while_the_program_waits():
    screen = make_screen('SHOW "MAIN"\nWHILE CLICKS<1\n  WAIT 1\nWEND\nPRINT "DONE"\nEND\n'
                         + HANDLERS + DESIGN)
    run_frames(screen, 3)
    click(screen, *client(screen, "MAIN", 10, 10))
    run_frames(screen, 3)
    assert screen.terminal.text().startswith("DONE")
    screen.close()


def test_text_area_and_tab_focus():
    screen = make_screen('WINDOW "W", "T", 0, 20, 120, 80\nWIDGET "W", "TEXTAREA", "TA", 2, 2, 100, 45\n'
                         'SHOW "W"')
    run_frames(screen, 2)
    screen.handle_events([text("AB"), key("enter"), text("CD"), key("left"), key("backspace")])
    assert prop(screen, "TA", "TEXT") == "AB\nD"
    screen.handle_events([key("up"), key("end"), text("!")])
    assert prop(screen, "TA", "TEXT") == "AB!\nD"
    screen.close()


def test_msgbox_waits_for_ok():
    screen = make_screen('MSGBOX "HI"\nPRINT "AFTER"')
    run_frames(screen, 3)
    assert screen.terminal.text() == "" and screen.gui.has_visible_windows()
    screen.handle_events([key("enter")])
    run_frames(screen, 3)
    assert screen.terminal.text().startswith("AFTER")
    screen.close()


def test_dragging_the_title_bar_moves_the_window():
    screen = start()
    w = screen.gui.windows["MAIN"]
    screen.handle_events([Event("mouse_down", x=30, y=25), Event("mouse_move", x=50, y=45),
                          Event("mouse_up", x=50, y=45)])
    assert (w.props["X"], w.props["Y"]) == (30, 40)
    screen.close()


def test_errors():
    def error(source):
        screen = make_screen(source)
        run_frames(screen, 3)
        screen.close()
        assert screen._pending_result.kind == ERROR
        return screen._pending_result.message

    assert "no widget type SLIDERX" in error('WINDOW "W","T",0,0,9,9\nWIDGET "W","SLIDERX","S",0,0,9,9')
    assert "name in use: W" in error('WINDOW "W","T",0,0,9,9\nWINDOW "W","T",0,0,9,9')
    assert "UNDEFINED FUNCTION" in error('WINDOW "W","T",0,0,9,9\nHANDLER "W","CLOSE","NOPE"')
    assert "no property FOO" in error('WINDOW "W","T",0,0,9,9\nSETPROP "W","FOO",1')
    assert "TYPE MISMATCH" in error('WINDOW "W","T",0,0,9,9\nSETPROP "W","TITLE",1')
    assert "TYPE MISMATCH" in error('WINDOW "W","T",0,0,9,9\nPRINT GETPROP("W","TITLE")')
    assert "W has no event CLICK" in error(
        'WINDOW "W","T",0,0,9,9\nHANDLER "W","CLICK","F"\nFUNCTION F()\nEND FUNCTION')


def test_widgets_can_be_added_from_python():
    @register_widget
    class Meter(Widget):
        TYPE = "METER"
        PROPERTIES = (PropertySpec("LEVEL", INT, 3),)

        def draw(self, ui, x, y, focused):
            pass

    assert "METER" in widget_types()
    screen = make_screen('WINDOW "W","T",0,0,99,99\nWIDGET "W","METER","M",1,1,20,8\n'
                         'SETPROP "M","LEVEL",7\nPRINT GETPROP("M","LEVEL")')
    run_frames(screen, 3)
    assert screen.terminal.text().startswith("7")
    screen.close()
