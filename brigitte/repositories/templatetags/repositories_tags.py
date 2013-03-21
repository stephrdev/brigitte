# -*- coding: utf-8 -*-
from django import template
from django.template.defaulttags import url


register = template.Library()


@register.tag(name='repo_url')
def do_repo_url(parser, token):
    func_name, view_name, token_parts = token.contents.split(' ', 2)

    token_parts = token_parts.split(' ', 1)

    if len(token_parts) > 1:
        repo_obj_name = token_parts[0]
        new_token = token_parts[1]
    else:
        repo_obj_name = token_parts[0]
        new_token = ''

    return url(parser, template.Token(token.token_type,
        '%s %s %s.user.username %s.slug %s' % (
            func_name,
            view_name,
            repo_obj_name,
            repo_obj_name,
            new_token
        )
    ))
