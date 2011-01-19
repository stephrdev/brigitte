from django import template
register = template.Library()

@register.filter
def truncate(str):
    return str[:7]