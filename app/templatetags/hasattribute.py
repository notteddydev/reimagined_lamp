from django import template

from typing import Any

register = template.Library()

def hasattribute(value: object, arg: Any) -> bool:
    """
    Determines whether an object has an attribute dynamically from a string name.
    """
    return hasattr(value, str(arg))

register.filter("hasattribute", hasattribute)