"""Widget types by name (GUI.md 7).

    register_widget(SliderWidget)       # a Widget subclass with TYPE = "SLIDER"

The standard widgets are registered the same way. The GUI designer builds its
toolbox and property list from this table.
"""

_TYPES = {}


def register_widget(cls):
    name = cls.TYPE.upper()
    if not name:
        raise ValueError("widget class without TYPE")
    _TYPES[name] = cls
    return cls


def widget_class(type_name):
    return _TYPES.get(type_name.upper())


def widget_types():
    """Registered type names in the order of registration."""
    return list(_TYPES)
