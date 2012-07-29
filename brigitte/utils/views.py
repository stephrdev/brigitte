# -*- coding: utf-8 -*-
from django import http
from django.conf import settings
from django.template import Context, loader


def server_error(request, template_name='500.html'):
    """ needed for rendering 500 pages with style. """
    t = loader.get_template(template_name)
    return http.HttpResponseServerError(t.render(Context({
        'request': request,
        'STATIC_URL': settings.STATIC_URL,
    })))
