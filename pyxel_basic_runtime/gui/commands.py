"""BASIC commands and functions of the GUI (GUI.md 4)."""

from py_basic_core import WaitUntil
from py_basic_core.errors import ILLEGAL_FUNCTION_CALL, TYPE_MISMATCH, UNDEFINED_FUNCTION

from .manager import GuiError
from .widget import PropertyError


def install(runtime, gui, check_handlers=True):
    """Register the GUI commands for the GuiManager ``gui``.

    check_handlers: HANDLER requires the function to exist. A GUI designer reading
    only the design part of a program passes False.
    """

    def guard(ctx, action):
        try:
            return action()
        except GuiError as e:
            raise ctx.error(ILLEGAL_FUNCTION_CALL, e.detail)
        except PropertyError as e:
            if e.kind == "type":
                raise ctx.error(TYPE_MISMATCH, str(e))
            raise ctx.error(ILLEGAL_FUNCTION_CALL, "no property " + str(e))

    def name_arg(ctx, value):
        return ctx.expect_str(value).upper()

    def window(ctx, args):
        """WINDOW name$, title$, x, y, w, h"""
        name, title = name_arg(ctx, args[0]), ctx.expect_str(args[1])
        x, y, w, h = (ctx.expect_int(v) for v in args[2:6])
        guard(ctx, lambda: gui.define_window(name, title, x, y, w, h))

    def widget(ctx, args):
        """WIDGET window$, type$, name$, x, y, w, h"""
        win, kind, name = (name_arg(ctx, v) for v in args[:3])
        x, y, w, h = (ctx.expect_int(v) for v in args[3:7])
        guard(ctx, lambda: gui.add_widget(win, kind, name, x, y, w, h))

    def set_property(ctx, args):
        """PROPERTY / SETPROP name$, property$, value"""
        name, prop = name_arg(ctx, args[0]), name_arg(ctx, args[1])

        def action():
            obj = gui.find(name)
            if prop == "VISIBLE" and obj in gui.windows.values():
                obj.set(prop, args[2])               # checks the value
                gui.set_window_visible(obj, args[2])
            else:
                obj.set(prop, args[2])
        guard(ctx, action)

    def handler(ctx, args):
        """HANDLER name$, event$, function$"""
        name, event, function = (name_arg(ctx, v) for v in args)
        if check_handlers and not ctx.runtime.has_function(function):
            raise ctx.error(UNDEFINED_FUNCTION, function)
        guard(ctx, lambda: gui.set_handler(name, event, function))

    def show(ctx, args):
        name = name_arg(ctx, args[0])
        guard(ctx, lambda: gui.show(name))

    def hide(ctx, args):
        name = name_arg(ctx, args[0])

        def action():
            obj = gui.find(name)
            if obj not in gui.windows.values():
                raise GuiError("not a window: " + name)
            gui.hide(obj)
        guard(ctx, action)

    def msgbox(ctx, args):
        """MSGBOX text$[, title$]: waits until OK is pressed."""
        text = args[0] if isinstance(args[0], str) else str(ctx.expect_int(args[0]))
        title = ctx.expect_str(args[1]) if len(args) > 1 else "MESSAGE"
        return WaitUntil(gui.message_box(text, title))

    def get_property(ctx, args, string):
        name, prop = name_arg(ctx, args[0]), name_arg(ctx, args[1])
        value = guard(ctx, lambda: gui.find(name).get(prop))
        if isinstance(value, str) != string:
            raise ctx.error(TYPE_MISMATCH, prop)
        return value

    for name, fn, lo, hi in (
        ("WINDOW", window, 6, 6),
        ("WIDGET", widget, 7, 7),
        ("PROPERTY", set_property, 3, 3),
        ("SETPROP", set_property, 3, 3),
        ("HANDLER", handler, 3, 3),
        ("SHOW", show, 1, 1),
        ("HIDE", hide, 1, 1),
        ("MSGBOX", msgbox, 1, 2),
    ):
        runtime.register_command(name, fn, lo, hi)
    runtime.register_function("GETPROP", lambda ctx, args: get_property(ctx, args, False), 2, 2)
    runtime.register_function("GETPROP$", lambda ctx, args: get_property(ctx, args, True), 2, 2)
