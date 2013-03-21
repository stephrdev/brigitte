# -*- coding: utf-8 -*-
from django.conf.urls.defaults import url, patterns


urlpatterns = patterns('brigitte.trees.views',
    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/tree/(?P<path>.+)$',
        'tree', name='trees_tree'),
    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/tree/$',
        'tree', name='trees_tree_root'),
)
