"""GUI for BASIC programs: windows and widgets in the style of the editor (GUI.md).

The standard widgets are registered when this package is imported. Add more
with register_widget() (a Widget subclass with TYPE, PROPERTIES and EVENTS).
"""

from . import widgets  # noqa: F401  (registers the first standard widgets)
from .listbox import ListBox
from .manager import GuiError, GuiManager
from .picture import PictureBox
from .registry import register_widget, widget_class, widget_types
from .scrollbar import HScrollBar, VScrollBar
from .widget import INT, STR, PropertyError, PropertySpec, Widget
from .window import GuiWindow

for _cls in (ListBox, PictureBox, HScrollBar, VScrollBar):    # the order of the toolbox
    register_widget(_cls)

DESIGN_FUNCTION = "GUI_DESIGN"     # called before the main program when it exists (GUI.md 5)

__all__ = [
    "GuiError", "GuiManager", "GuiWindow", "PropertyError", "PropertySpec", "Widget",
    "ListBox", "PictureBox", "HScrollBar", "VScrollBar",
    "INT", "STR", "register_widget", "widget_class", "widget_types", "DESIGN_FUNCTION",
]
