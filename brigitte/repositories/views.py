from django.http import Http404, HttpResponse
from django.utils.translation import gettext_lazy as _
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.template.defaultfilters import slugify

from brigitte.repositories.models import Repository
from brigitte.repositories.forms import RepositoryForm, RepositoryUserFormSet

@login_required
def repositories_manage_list(request):
    return render(request, 'repositories/repository_manage_list.html', {
        'repository_list': Repository.objects.manageable_repositories(
            request.user),
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

