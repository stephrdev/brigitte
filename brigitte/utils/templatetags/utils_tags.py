# -*- coding: utf-8 -*-
from django import template

from brigitte.utils.highlight import pygmentize


register = template.Library()


@register.filter
def pygmentize_diff(blob):
    try:
        return pygmentize('diff', blob)
    except:
        return blob
