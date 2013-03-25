# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *
from django.contrib import admin


handler500 = 'brigitte.utils.views.server_error'

admin.autodiscover()

urlpatterns = patterns('',
    (r'^admin/', include(admin.site.urls)),
    (r'^', include('brigitte.accounts.urls')),
    (r'^accounts/', include('userprofiles.urls')),
    (r'^', include('brigitte.repositories.urls')),
    (r'^', include('brigitte.commits.urls')),
    (r'^', include('brigitte.trees.urls')),
)
