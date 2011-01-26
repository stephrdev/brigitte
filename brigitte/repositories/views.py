from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.defaultfilters import slugify

from brigitte.repositories.models import Repository
from brigitte.repositories.forms import RepositoryForm, RepositoryUserFormSet
from brigitte.repositories.utils import pygmentize, build_path_breadcrumb

@login_required
def repositories_manage_list(request):
    return render(request, 'repositories/repository_manage_list.html', {
        'repository_list': Repository.objects.manageable_repositories(
            request.user),
    })

@login_required
def repositories_user(request, user):
    user = get_object_or_404(User, username=user)
    return render(request, 'repositories/repository_user.html', {
        'user': user,
        'repositories': user.repository_set.public_repositories(),
    })

@login_required
def repositories_manage_change(request, user, slug):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)
    if not repo.user_is_admin(request.user):
        raise Http404

    if request.method == 'POST':
        if request.POST.get('method', None) == 'add_repouser':
            result = False
            error_msg = 'No error message'

            try:
                user = User.objects.get(email=request.POST.get('email', None))
                if repo.user == user:
                    error_msg = 'You cannot re-add the repository owner.'
                elif user.repositoryuser_set.filter(repo=repo).exists():
                    error_msg = 'User already added to repository'
                else:
                    repo.repositoryuser_set.create(user=user)
                    result = True
            except User.DoesNotExist:
                error_msg ='Invalid email address'

            return HttpResponse('{"result": "%s", "error_msg": "%s"}' % (
                int(result), error_msg)
            )
        repo_form = RepositoryForm(
            request.POST, instance=repo, prefix='repository')
        users_formset = RepositoryUserFormSet(request.POST, prefix='users')
        if repo_form.is_valid():
            repo_form.save()

            if users_formset.is_valid():
                for instance in users_formset.save(commit=False):
                    if not instance.pk:
                        instance.repo = repo
                    instance.save()

            messages.success(request, _('Repository updated.'))
            return redirect('repositories_manage_list')
    else:
        repo_form = RepositoryForm(instance=repo, prefix='repository')
        users_formset = RepositoryUserFormSet(
            prefix='users',
            queryset=repo.alterable_users
        )

    return render(request, 'repositories/repository_manage_change.html', {
        'repo': repo,
        'form': repo_form,
        'users': users_formset,
    })

@login_required
def repositories_manage_add(request):
    if request.method == 'POST':
        form = RepositoryForm(request.POST)
        if form.is_valid():
            repo = form.save(commit=False)
            repo.user = request.user
            repo.slug = slugify(repo.title)
            repo.save()
            repo.repositoryuser_set.create(
                user=request.user,
                can_read=True,
                can_write=True,
                can_admin=True
            )
            messages.success(request, _('Repository added.'))
            return redirect('repositories_manage_list')
    else:
        form = RepositoryForm()

    return render(request, 'repositories/repository_manage_add.html', {
        'form': form,
    })

def repositories_list(request):
    return render(request, 'repositories/repository_list.html', {
        'repository_list': Repository.objects.public_repositories(),
    })

def repositories_summary(request, user, slug):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)

    return render(request, 'repositories/repository_summary.html', {
        'repository': repo,
    })


def repositories_commits(request, user, slug, branchtag):
    count = 10
    page = int(request.GET.get('page', 1))
    skip = (page * count) - count
    if skip < 0:
        skip = 0
    repo = get_object_or_404(Repository, user__username=user, slug=slug)
    commits = repo.get_commits(count=count, skip=skip, head=branchtag)
    return render(request, 'repositories/repository_commits.html', {
        'repository': repo,
        'commits': commits,
        'branchtag': branchtag,
        'next_page': page + 1,
        'prev_page': page - 1,
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

def repositories_commit_archive(request, user, slug, sha):
    repo = get_object_or_404(Repository, user__username=user, slug=slug)
    commit = repo.get_commit(sha)

    try:
        archive = commit.get_archive()
        response = HttpResponse(archive['data'].getvalue(),
            mimetype=archive['mime'])
        response['Content-Disposition'] = \
            'attachment; filename="%s-%s.zip"' \
                % (repo.slug, archive['filename'])
        return response
    except:
        raise Http404

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
            'breadcrumb': build_path_breadcrumb(path)
        })

    else:
        file_obj = commit.get_file(path)
        if file_obj is None:
            raise Http404

        file_blob_pygmentized = pygmentize(
            path.rsplit('.', 1)[-1], file_obj.content)

        return render(request, 'repositories/repository_file.html', {
            'repository': repo,
            'commit': commit,
            'file_path': path,
            'file_obj': file_obj,
            'file_lines': range(1, file_obj.content.count('\n') + 1),
            'file_blob_pygmentized': file_blob_pygmentized,
            'breadcrumb': build_path_breadcrumb(path)
        })

