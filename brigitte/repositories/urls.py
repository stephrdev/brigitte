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
    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/delete/$',
        'repositories_manage_delete',
        name='repositories_manage_delete'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/$', 'repositories_summary',
        name='repositories_summary'),

    url(r'^(?P<user>[\w-]+)/$', 'repositories_user',
        name='repositories_user'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/$',
        'repositories_commit', name='repositories_commit'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commits/(?P<branchtag>.+)$',
        'repositories_commits', name='repositories_commits'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/tree/(?P<path>.+)$',
        'repositories_commit_tree', name='repositories_commit_tree'),
    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/commit/(?P<sha>[\w-]+)/tree/$',
        'repositories_commit_tree', name='repositories_commit_tree_root'),

    url(r'^(?P<user>[\w-]+)/(?P<slug>[\w-]+)/archive/(?P<sha>[\w-]+)/$',
        'repositories_commit_archive', name='repositories_commit_archive'),
)

