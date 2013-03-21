# -*- coding: utf-8 -*-
from django.conf.urls.defaults import url, patterns


urlpatterns = patterns('brigitte.commits.views',
    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/$',
        'commit', name='commits_commit'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commits/(?P<branchtag>.+)$',
        'commits', name='commits_commits'),
)
