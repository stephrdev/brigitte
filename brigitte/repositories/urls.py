from django.conf.urls.defaults import *

urlpatterns = patterns('brigitte.repositories.views',
        url(r'^$', 'list', name='repository_list'),
        url(r'^(?P<slug>[\w-]+)/$', 'summary', name='repository_summary'),
)

