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

def repositories_tree(request, user, slug, sha, path=None):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)
    commit = repo.get_commit(sha)

    if not commit:
        raise Http404

    lstree = commit.get_tree(path)
    if lstree is None:
        raise Http404


    return render(request, 'repositories/repository_tree.html', {
        'repository': repo,
        'commit': commit,
        'lstree': lstree,
    })

def repositories_file(request, user, slug, sha, filesha):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)
    commit = repo.get_commit(sha)

    if not commit:
        raise Http404

    filecontent = commit.get_filecontent(filesha)
    if filecontent is None:
        raise Http404

    return render(request, 'repositories/repository_file.html', {
        'repository': repo,
        'commit': commit,
        'filecontent': filecontent,
    })
