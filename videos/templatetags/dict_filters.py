# videos/templatetags/dict_filters.py
from django import template

register = template.Library()

@register.filter
def dict_get(dict_obj, key):
    return dict_obj.get(key, '')

@register.filter
def dict_get(dictionary, key):
    """Return the value of a dictionary for the given key, or None if not found."""
    if dictionary and key in dictionary:
        return dictionary[key]
    return None

