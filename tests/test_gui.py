"""GUI of BASIC programs: windows, widgets, events (GUI.md)."""

import pyxel
from helpers import key, make_screen, run_frames, text

from retro_basic_runtime import ENDED, ERROR, Event
from retro_basic_runtime.gui import INT, PropertySpec, Widget, register_widget, widget_types
from retro_basic_runtime.gui.style import BAR_H

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


MORE = """
SHOW "W"
FUNCTION L_CHANGE()
    PRINT "SEL ";GETPROP("L","INDEX");" ";GETPROP$("L","ITEM")
END FUNCTION
FUNCTION L_ENTER()
    PRINT "OPEN ";GETPROP$("L","ITEM")
END FUNCTION
FUNCTION S_CHANGE()
    PRINT "S";GETPROP("S","VALUE")
END FUNCTION
FUNCTION P_CLICK()
    PRINT "P";GETPROP("P","MOUSEX");",";GETPROP("P","MOUSEY")
END FUNCTION
FUNCTION GUI_DESIGN()
    WINDOW "W", "T", 0, 0, 200, 150
    WIDGET "W", "LISTBOX", "L", 0, 0, 80, 43
    PROPERTY "L", "ITEMS", "A" + CHR$(10) + "B" + CHR$(10) + "C" + CHR$(10) + "D" + CHR$(10) + "E"
    WIDGET "W", "HSCROLLBAR", "S", 90, 0, 80, 7
    PROPERTY "S", "MAX", 10
    PROPERTY "S", "PAGE", 2
    WIDGET "W", "VSCROLLBAR", "V", 180, 0, 7, 60
    WIDGET "W", "PICTUREBOX", "P", 90, 20, 32, 32
    HANDLER "L", "CHANGE", "L_CHANGE"
    HANDLER "L", "ENTER", "L_ENTER"
    HANDLER "S", "CHANGE", "S_CHANGE"
    HANDLER "P", "CLICK", "P_CLICK"
END FUNCTION
"""


def output(screen):
    return screen.terminal.text()


def test_list_box_selection_scroll_and_double_click():
    screen = make_screen(MORE)
    run_frames(screen, 3)
    lst = screen.gui.find("L")
    assert lst.get("COUNT") == 5 and lst.get("INDEX") == -1 and lst.get("ITEM") == ""
    assert lst.rows == 3
    click(screen, *client(screen, "W", 10, 2 + 13 + 5))        # the second row
    assert lst.get("ITEM") == "B" and "SEL 1 B" in output(screen)
    click(screen, *client(screen, "W", 10, 2 + 13 + 5))        # again: a double click
    assert "OPEN B" in output(screen)
    screen.handle_events([key("end")])                          # the list box has the focus
    run_frames(screen, 3)
    assert lst.get("INDEX") == 4 and lst.top == 2 and "SEL 4 E" in output(screen)
    x, y = client(screen, "W", 10, 10)
    screen.handle_events([Event("wheel", x=x, y=y, dy=1)])
    assert lst.top == 0
    click(screen, *client(screen, "W", 76, 40))                 # the bar's down arrow
    assert lst.top == 1 and lst.get("INDEX") == 4               # scrolling keeps the selection
    screen.close()


def test_list_box_properties_from_basic():
    screen = make_screen(MORE.replace('SHOW "W"', 'SHOW "W"\nSETPROP "L","INDEX",2\n'
                                      'PRINT GETPROP$("L","ITEM");GETPROP("L","COUNT")\n'
                                      'SETPROP "L","ITEMS","X"\nPRINT GETPROP("L","INDEX")\n'
                                      'SETPROP "L","ITEMS",""\nPRINT GETPROP("L","COUNT")'))
    run_frames(screen, 3)
    assert output(screen).split()[:3] == ["C5", "-1", "0"]
    assert "SEL" not in output(screen)                         # SETPROP reports no event
    screen.close()


def test_scroll_bars():
    screen = make_screen(MORE)
    run_frames(screen, 3)
    bar = screen.gui.find("S")
    click(screen, *client(screen, "W", 90 + 77, 3))            # right arrow: STEP
    assert bar.get("VALUE") == 1 and "S1" in output(screen)
    click(screen, *client(screen, "W", 90 + 60, 3))            # the track right of the thumb: PAGE
    assert bar.get("VALUE") == 3
    x, y = client(screen, "W", 90 + 10, 3)                      # hold the left arrow: repeats
    screen.handle_events([Event("mouse_down", x=x, y=y)])
    run_frames(screen, 40)
    screen.handle_events([Event("mouse_up", x=x, y=y)])
    assert bar.get("VALUE") == 0
    ts, size = bar._thumb()                                     # drag the thumb to the end
    x, y = client(screen, "W", ts + 1, 3)
    screen.handle_events([Event("mouse_down", x=x, y=y), Event("mouse_move", x=x + 200, y=y),
                          Event("mouse_up", x=x + 200, y=y)])
    run_frames(screen, 3)
    assert bar.get("VALUE") == 10
    screen.handle_events([key("home")])
    assert bar.get("VALUE") == 0
    bar.set("VALUE", 99)                                        # kept between MIN and MAX
    assert bar.get("VALUE") == 10
    bar.set("MAX", 5)
    assert bar.get("VALUE") == 5
    vbar = screen.gui.find("V")
    click(screen, *client(screen, "W", 182, 57))               # down arrow of the vertical bar
    assert vbar.get("VALUE") == 1
    screen.close()


def test_picture_box_click_and_drag():
    screen = make_screen(MORE.replace('HANDLER "P", "CLICK", "P_CLICK"',
                                      'HANDLER "P", "CLICK", "P_CLICK"\n'
                                      '    HANDLER "P", "DRAG", "P_CLICK"'))
    run_frames(screen, 3)
    x, y = client(screen, "W", 95, 27)
    screen.handle_events([Event("mouse_down", x=x, y=y)])
    run_frames(screen, 3)
    assert "P5,7" in output(screen)
    screen.handle_events([Event("mouse_move", x=x + 3, y=y + 1)])
    run_frames(screen, 3)
    screen.handle_events([Event("mouse_up", x=x + 3, y=y + 1)])
    assert "P8,8" in output(screen)
    screen.close()


def test_errors_of_the_new_widgets():
    def error(lines):
        screen = make_screen('WINDOW "W","T",0,0,99,99\n' + lines)
        run_frames(screen, 3)
        screen.close()
        assert screen._pending_result.kind == ERROR
        return screen._pending_result.message

    assert "read-only property ITEM" in error('WIDGET "W","LISTBOX","L",0,0,50,50\n'
                                              'SETPROP "L","ITEM","X"')
    assert "bad value INDEX=3" in error('WIDGET "W","LISTBOX","L",0,0,50,50\n'
                                        'SETPROP "L","ITEMS","A"\nSETPROP "L","INDEX",3')
    assert "bad value IMAGE=3" in error('WIDGET "W","PICTUREBOX","P",0,0,50,50\n'
                                        'SETPROP "P","IMAGE",3')


def test_background_colors():
    screen = make_screen('''
WINDOW "W", "T", 0, 0, 120, 80
WIDGET "W", "LABEL", "L", 0, 0, 60, 13
WIDGET "W", "BUTTON", "B", 0, 20, 40, 16
WIDGET "W", "VSCROLLBAR", "S", 100, 0, 7, 60
SHOW "W"
PRINT GETBGCOLOR("W"); GETBGCOLOR("L"); GETBGCOLOR("B"); GETBGCOLOR("S")
SETBGCOLOR "W", 3
SETBGCOLOR "L", 10
SETPROP "B", "BGCOLOR", 8
PRINT GETBGCOLOR("W"); GETBGCOLOR("L"); GETPROP("B", "BGCOLOR")
SETBGCOLOR "L", -1
PRINT GETBGCOLOR("L")
''')
    run_frames(screen, 3)
    assert screen.terminal.text().split()[:3] == ["7-171", "3108", "-1"]
    screen.draw()
    w = screen.gui.windows["W"]
    ox, oy = w.client_origin
    assert pyxel.pget(ox + 80, oy + 50) == 3                       # the window's client area
    assert pyxel.pget(ox + 38, oy + 30) == 8                       # inside the button
    screen.close()


def test_background_color_errors():
    def error(lines):
        screen = make_screen('WINDOW "W","T",0,0,99,99\n' + lines)
        run_frames(screen, 3)
        screen.close()
        return screen._pending_result.message

    assert "bad value BGCOLOR=16" in error('SETBGCOLOR "W", 16')
    assert "bad value BGCOLOR=-2" in error('SETBGCOLOR "W", -2')
    assert "no window or widget X" in error('PRINT GETBGCOLOR("X")')
    assert "TYPE MISMATCH" in error('SETBGCOLOR "W", "RED"')
