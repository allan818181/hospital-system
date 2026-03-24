from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using the key"""
    return dictionary.get(key)

@register.filter
def get_range(value):
    """Get a range of numbers from 0 to value-1"""
    return range(value)

@register.filter
def get_item(dictionary, key):
    """
    Filter - returns a value from a dictionary using the given key
    Usage (in template):
    {{ dictionary|get_item:key }}
    """
    try:
        return dictionary.get(key)
    except (AttributeError, TypeError):
        return None

@register.filter
def filter_by_appointment(prescriptions, appointment):
    """Filters prescriptions by appointment"""
    return prescriptions.filter(appointment=appointment) 