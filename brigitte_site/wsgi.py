# -*- coding: utf-8 -*-
import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "brigitte_site.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
