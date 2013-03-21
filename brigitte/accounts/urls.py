# -*- coding: utf-8 -*-
from django.conf.urls.defaults import url, patterns


urlpatterns = patterns('brigitte.accounts.views',
    url(r'^accounts/keys/$', 'keys_list', name='accounts_keys_list'),
    url(r'^accounts/keys/add/$', 'keys_add', name='accounts_keys_add'),
    url(r'^accounts/keys/(?P<pk>\d+)/$', 'keys_change', name='accounts_keys_change'),
    url(r'^accounts/keys/(?P<pk>\d+)/delete/$', 'keys_delete', name='accounts_keys_delete'),

    url(r'^accounts/profile/$', 'profile', name='accounts_profile'),
    url(r'^(?P<user>[\w-]+)/$', 'public_profile', name='accounts_public_profile'),
)
