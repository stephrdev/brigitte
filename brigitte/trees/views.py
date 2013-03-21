# -*- coding: utf-8 -*-
from django.core.serializers.json import DjangoJSONEncoder
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.template.defaultfilters import timesince
from django.utils import simplejson

from brigitte.repositories.decorators import repository_view
from brigitte.trees.utils import build_path_breadcrumb
from brigitte.utils.highlight import pygmentize


@repository_view()
def tree(request, repo, sha, path=None):
    try:
        commit = repo.get_commit(sha)
    except KeyError:
        raise Http404

    if not path or path[-1] == '/':
        if request.is_ajax() and 'commits' in request.GET:
            tree = commit.get_tree(path, commits=True).tree
            tree_elements = []
            for entry in tree:
                tree_elements.append({
                    'tree_id': entry['sha'],
                    'id': entry['commit'].id,
                    'author': entry['commit'].author,
                    'commit_date': entry['commit'].commit_date,
                    'since': timesince(entry['commit'].commit_date),
                })
            return HttpResponse(simplejson.dumps(tree_elements,
                cls=DjangoJSONEncoder), mimetype='application/json')

        try:
            tree = commit.get_tree(path)
        except KeyError:
            raise Http404

        return render(request, 'trees/tree.html', {
            'repository': repo,
            'commit': commit,
            'tree': tree,
            'breadcrumb': build_path_breadcrumb(path)
        })

    else:
        try:
            file_obj = commit.get_file(path)
        except KeyError:
            raise Http404

        file_blob_pygmentized = pygmentize(
            path.rsplit('.', 1)[-1], file_obj.content)

        return render(request, 'trees/file.html', {
            'repository': repo,
            'commit': commit,
            'file_path': path,
            'file_obj': file_obj,
            'file_lines': range(1, file_obj.content.count('\n') + 1),
            'file_blob_pygmentized': file_blob_pygmentized,
            'breadcrumb': build_path_breadcrumb(path)
        })
