"""GUI for BASIC programs: windows and widgets in the style of the editor (GUI.md).

The standard widgets are registered when this package is imported. Add more
with register_widget() (a Widget subclass with TYPE, PROPERTIES and EVENTS).
"""

from . import widgets  # noqa: F401  (registers the standard widgets)
from .manager import GuiError, GuiManager
from .registry import register_widget, widget_class, widget_types
from .widget import INT, STR, PropertyError, PropertySpec, Widget
from .window import GuiWindow

DESIGN_FUNCTION = "GUI_DESIGN"     # called before the main program when it exists (GUI.md 5)

__all__ = [
    "GuiError", "GuiManager", "GuiWindow", "PropertyError", "PropertySpec", "Widget",
    "INT", "STR", "register_widget", "widget_class", "widget_types", "DESIGN_FUNCTION",
]
