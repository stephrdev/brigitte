from django.http import Http404
from django.shortcuts import render, get_object_or_404

from brigitte.repositories.models import Repository

def repositories_list(request):
    return render(request, 'repositories/repository_list.html', {
        'repository_list': Repository.objects.all(),
    })

def repositories_summary(request, user, slug):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)

    return render(request, 'repositories/repository_summary.html', {
        'repository': repo,
    })

def repositories_commit(request, user, slug, sha):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)
    commit = repo.get_commit(sha)

    if not commit:
        raise Http404

    return render(request, 'repositories/repository_commit.html', {
        'repository': repo,
        'commit': commit,
    })

def repositories_commit_tree(request, user, slug, sha, path=None):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)
    commit = repo.get_commit(sha)

    if not commit:
        raise Http404

    if not path or path[-1] == '/':
        tree = commit.get_tree(path)
        if tree is None:
            raise Http404

        return render(request, 'repositories/repository_tree.html', {
            'repository': repo,
            'commit': commit,
            'tree': tree,
        })

    else:
        file_blob = commit.get_file(path)
        if file_blob is None:
            raise Http404

        return render(request, 'repositories/repository_file.html', {
            'repository': repo,
            'commit': commit,
            'file': file_blob,
        })

