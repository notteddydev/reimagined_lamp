from django import template

from typing import Any

register = template.Library()

def getattribute(value: object, arg: Any) -> Any:
    """
    Gets an attribute of an object dynamically from a string name.
    """
    return getattr(value, str(arg))

register.filter("getattribute", getattribute)