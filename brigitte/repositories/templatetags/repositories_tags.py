from django import template
from brigitte.repositories import pygmentize

register = template.Library()

@register.filter
def pygmentize_diff(blob):
    try:
        return pygmentize('diff', blob)
    except:
        return blob


