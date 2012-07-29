from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

admin.autodiscover()

urlpatterns = patterns('',
    (r'^accounts/', include('brigitte.accounts.urls')),
    (r'^accounts/', include('userprofiles.urls')),
    (r'^admin/', include(admin.site.urls)),
    (r'^', include('brigitte.repositories.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^site_media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
    urlpatterns += staticfiles_urlpatterns()
