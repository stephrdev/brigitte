# -*- coding: utf-8 -*-
from django.http import Http404
from django.shortcuts import render

from brigitte.repositories.decorators import repository_view


@repository_view()
def commits(request, repo, branchtag):
    count = 10

    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    skip = (page * count) - count
    if skip < 0:
        skip = 0
    commits = repo.get_commits(count=count + 1, skip=skip, head=branchtag)
    if not commits:
        raise Http404

    return render(request, 'commits/commits.html', {
        'repository': repo,
        'commits': commits[:count],
        'branchtag': branchtag,
        'next_page': page + 1 if len(commits) > count else None,
        'prev_page': page - 1 if page > 1 else None,
    })


@repository_view()
def commit(request, repo, sha):
    try:
        commit = repo.get_commit(sha)
    except KeyError:
        raise Http404

    return render(request, 'commits/commit.html', {
        'repository': repo,
        'commit': commit,
    })


#@repository_view()
#def archive(request, repo, sha):
#    commit = repo.get_commit(sha)
#
#    try:
#        archive = commit.get_archive()
#        response = HttpResponse(archive['data'].getvalue(),
#            mimetype=archive['mime'])
#        response['Content-Disposition'] = \
#            'attachment; filename="%s-%s.zip"' \
#                % (repo.slug, archive['filename'])
#        return response
#    except:
#        raise Http404
