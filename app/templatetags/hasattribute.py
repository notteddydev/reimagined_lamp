from django import template

register = template.Library()

def hasattribute(value, arg):
    """Determines whether an object has an attribute dynamically from a string name"""

    return hasattr(value, str(arg))

register.filter('hasattribute', hasattribute)