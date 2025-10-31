# videos/templatetags/time_filters.py
from django import template

register = template.Library()

@register.filter
def seconds_to_hms(value):
    try:
        total_seconds = int(value)
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"
    except:
        return "00:00"
