from django.conf.urls.defaults import *

urlpatterns = patterns('brigitte.repositories.views',
    url(r'^$', 'repositories_list', name='repositories_list'),

    url(r'^manage/$', 'repositories_manage_list',
        name='repositories_manage_list'),
    url(r'^manage/add/$', 'repositories_manage_add',
        name='repositories_manage_add'),
    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/manage/$',
        'repositories_manage_change',
        name='repositories_manage_change'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/$', 'repositories_summary',
        name='repositories_summary'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/$',
        'repositories_commit', name='repositories_commit'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/tree/(?P<path>.+)$',
        'repositories_commit_tree', name='repositories_commit_tree'),
    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/tree/$',
        'repositories_commit_tree', name='repositories_commit_tree_root'),
)

