"""Base class of GUI widgets and their property / event definitions (GUI.md 3 / 7).

A widget type is a subclass of Widget that lists its PROPERTIES and EVENTS.
The runtime (BASIC commands) and the GUI designer both work from these lists,
so a widget registered later from Python (registry.register_widget) appears
everywhere without other changes.
"""

from dataclasses import dataclass

INT = "int"
STR = "str"


@dataclass(frozen=True)
class PropertySpec:
    name: str
    kind: str               # INT or STR (a 1 / 0 flag is INT)
    default: object
    choices: tuple = ()     # allowed values, empty for any
    readonly: bool = False  # read with GETPROP only; the widget sets it (not saved by the designer)


# Colors are palette numbers 0-15, like the drawing commands; -1 means none (transparent).
COLOR_CHOICES = tuple(range(16))
BG_CHOICES = (-1,) + COLOR_CHOICES


def bgcolor_property(default):
    """BGCOLOR: the background color (GUI.md 3), -1 for a transparent background."""
    return PropertySpec("BGCOLOR", INT, default, BG_CHOICES)


# Every widget has these.
COMMON_PROPERTIES = (
    PropertySpec("X", INT, 0),
    PropertySpec("Y", INT, 0),
    PropertySpec("W", INT, 60),
    PropertySpec("H", INT, 15),
    PropertySpec("ENABLED", INT, 1, (0, 1)),
    PropertySpec("VISIBLE", INT, 1, (0, 1)),
)


class PropertyError(Exception):
    """Unknown property (``kind`` "name"), a value of the wrong type ("type"),
    a value that is not allowed ("value") or a read-only property ("readonly")."""

    def __init__(self, kind, detail):
        super().__init__(detail)
        self.kind = kind


class Widget:
    TYPE = ""               # name used in BASIC: WIDGET "MAIN", "BUTTON", ...
    PROPERTIES = ()         # PropertySpec, ... in addition to COMMON_PROPERTIES
    EVENTS = ()             # event names, e.g. ("CLICK",)
    DEFAULT_SIZE = (60, 15)
    FOCUSABLE = False       # takes keyboard focus (Tab)

    def __init__(self, name):
        self.name = name
        self.window = None
        self.props = {spec.name: spec.default for spec in self.property_specs().values()}
        self.props["W"], self.props["H"] = self.DEFAULT_SIZE

    @classmethod
    def property_specs(cls):
        """Property name -> PropertySpec, common ones first."""
        return {spec.name: spec for spec in COMMON_PROPERTIES + tuple(cls.PROPERTIES)}

    # --- properties --------------------------------------------------------
    def get(self, name):
        if name not in self.props:
            raise PropertyError("name", name)
        return self.props[name]

    def set(self, name, value):
        spec = self.property_specs().get(name)
        if spec is None:
            raise PropertyError("name", name)
        if spec.readonly:
            raise PropertyError("readonly", name)
        if (spec.kind == STR) != isinstance(value, str):
            raise PropertyError("type", name)
        if spec.choices and value not in spec.choices:
            raise PropertyError("value", "%s=%r" % (name, value))
        if spec.kind == INT and name in ("W", "H"):
            value = max(1, value)
        self.props[name] = self.check(name, value)
        self.changed(name)

    def check(self, name, value):
        """The value to store for ``name``; raise PropertyError("value", ...) to refuse it."""
        return value

    def changed(self, name):
        """Called after a property was set (subclasses keep their state in step)."""

    @property
    def rect(self):
        p = self.props
        return p["X"], p["Y"], p["W"], p["H"]

    @property
    def visible(self):
        return bool(self.props["VISIBLE"])

    @property
    def enabled(self):
        return bool(self.props["ENABLED"])

    def contains(self, x, y):
        """(x, y) in window client coordinates."""
        wx, wy, w, h = self.rect
        return wx <= x < wx + w and wy <= y < wy + h

    # --- events ------------------------------------------------------------
    def fire(self, event):
        """Report an event; the window's manager queues the BASIC handler if there is one."""
        if self.window is not None:
            self.window.report(self, event)

    # --- input (coordinates are window client coordinates) -----------------
    def mouse_down(self, x, y):
        """Return True to keep receiving mouse_drag / mouse_up."""
        return False

    def mouse_drag(self, x, y):
        pass

    def mouse_up(self, x, y):
        pass

    def wheel(self, dy):
        """The mouse wheel over the widget (dy > 0: away from the user). Return True if used."""
        return False

    def key(self, ev):
        """A key or text Event while this widget has the focus. Return True if used."""
        return False

    def update(self, frame):
        """Called every frame while the window is shown (e.g. for key repeat of a held button)."""

    # --- drawing -----------------------------------------------------------
    def draw(self, ui, x, y, focused):
        """Draw at screen position (x, y). ``ui`` gives the font (ui.font) and the frame count."""
        raise NotImplementedError
