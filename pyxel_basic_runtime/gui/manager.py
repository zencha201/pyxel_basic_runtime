"""All GUI windows of a BASIC program: order, focus, input and events (GUI.md 2 / 4).

Names of windows and widgets are unique in the program. An event of a widget
(e.g. CLICK) queues the name of the BASIC function set with HANDLER; the BASIC
screen calls it when the program can take it.
"""

from collections import deque

from .registry import widget_class
from .window import GuiWindow, MessageWindow


class GuiError(Exception):
    """A GUI command was used wrongly; ``detail`` explains how."""

    def __init__(self, detail):
        super().__init__(detail)
        self.detail = detail


class Ui:
    """What widgets need to draw: the font and the frame count (for the caret)."""

    def __init__(self, font):
        self.font = font
        self.frame = 0


class GuiManager:
    def __init__(self, font):
        self.ui = Ui(font)
        self.windows = {}           # name -> GuiWindow
        self.objects = {}           # name -> GuiWindow or widget
        self.order = []             # visible windows, back to front
        self.handlers = {}          # (name, event) -> BASIC function name
        self.pending = deque()      # BASIC functions to call
        self.used = False           # a window has been shown
        self._captured = None       # window that got mouse_down

    # --- definition ------------------------------------------------------------
    def _check_new_name(self, name):
        if not name:
            raise GuiError("empty name")
        if name in self.objects:
            raise GuiError("name in use: " + name)

    def define_window(self, name, title, x, y, w, h):
        self._check_new_name(name)
        window = GuiWindow(name, self)
        window.props.update(TITLE=title, X=x, Y=y, W=max(1, w), H=max(1, h))
        self.windows[name] = window
        self.objects[name] = window
        return window

    def add_widget(self, window_name, type_name, name, x, y, w, h):
        window = self.windows.get(window_name)
        if window is None:
            raise GuiError("no window " + window_name)
        cls = widget_class(type_name)
        if cls is None:
            raise GuiError("no widget type " + type_name)
        self._check_new_name(name)
        widget = cls(name)
        widget.props.update(X=x, Y=y, W=max(1, w), H=max(1, h))
        window.add(widget)
        self.objects[name] = widget
        return widget

    def find(self, name):
        obj = self.objects.get(name)
        if obj is None:
            raise GuiError("no window or widget " + name)
        return obj

    def set_handler(self, name, event, function):
        obj = self.find(name)
        if event not in obj.EVENTS:
            raise GuiError("%s has no event %s" % (name, event))
        self.handlers[(name, event)] = function

    # --- showing ---------------------------------------------------------------
    def show(self, name):
        window = self.windows.get(name)
        if window is None:
            raise GuiError("no window " + name)
        window.props["VISIBLE"] = 1
        if window in self.order:
            self.order.remove(window)
        self.order.append(window)
        if window.focus is None:
            window.focus_first()
        self.used = True

    def hide(self, window):
        window.props["VISIBLE"] = 0
        if window in self.order:
            self.order.remove(window)
        if self._captured is window:
            self._captured = None

    def close(self, window):
        """The close box (or MSGBOX's OK): hide, then report CLOSE."""
        self.hide(window)
        if not isinstance(window, MessageWindow):
            self.fire(window, "CLOSE")

    def message_box(self, text, title):
        """Show a message window; returns a function telling whether it is closed."""
        window = MessageWindow(self, text, title)
        self.order.append(window)
        return lambda: window not in self.order

    def set_window_visible(self, window, visible):
        if visible:
            self.show(window.name)
        else:
            self.hide(window)

    @property
    def active(self):
        """The front window, which gets the keyboard."""
        return self.order[-1] if self.order else None

    def has_visible_windows(self):
        return bool(self.order)

    # --- events ----------------------------------------------------------------
    def fire(self, obj, event):
        function = self.handlers.get((obj.name, event))
        if function:
            self.pending.append(function)

    def next_handler(self):
        return self.pending.popleft() if self.pending else None

    # --- input -----------------------------------------------------------------
    def handle(self, ev):
        """Give an input Event to the windows. Returns True when they used it."""
        if not self.order:
            return False
        if ev.type == "mouse_down":
            window = self._window_at(ev.x, ev.y)
            if window is None:
                return False
            if not isinstance(self.active, MessageWindow):     # MSGBOX stays in front
                self.order.remove(window)
                self.order.append(window)
            if window is self.active:
                window.mouse_down(ev.x, ev.y)
                self._captured = window
            return True
        if ev.type == "mouse_move":
            if self._captured is not None:
                self._captured.mouse_drag(ev.x, ev.y)
            return self._captured is not None
        if ev.type == "mouse_up":
            window, self._captured = self._captured, None
            if window is not None:
                window.mouse_up(ev.x, ev.y)
            return window is not None
        if ev.type in ("key", "text"):
            self.active.key(ev)
            return True
        return False

    def _window_at(self, x, y):
        for window in reversed(self.order):
            if window.on_frame(x, y):
                return window
        return None

    # --- drawing ---------------------------------------------------------------
    def update(self):
        self.ui.frame += 1

    def draw(self):
        for window in self.order:
            window.draw_window(window is self.active)
