# -*- coding: utf-8 -*-
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect
from django.template.defaultfilters import slugify
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt

from brigitte.repositories.decorators import repository_view
from brigitte.repositories.forms import RepositoryForm, RepositoryUserFormSet
from brigitte.repositories.models import Repository


@login_required
def manage_list(request):
    return render(request, 'repositories/manage_list.html', {
        'repository_list': Repository.objects.manageable_repositories(
            request.user),
    })


@login_required
@repository_view(can_admin=True)
def manage_delete(request, repo):
    if 'magic' in request.GET and request.GET['magic'] == repo.title:
        repo.delete()
        messages.success(request, _('Repository "%s" deleted.') % repo.title)

        return redirect('accounts_profile')

    raise Http404


@csrf_exempt
@login_required
@repository_view(can_admin=True)
def manage_change(request, repo):
    if request.method == 'POST':
        if 'lookup_username' in request.POST:
            username = request.POST['lookup_username']
            result = {'error': False}

            try:
                user = User.objects.get(Q(Q(email=username) | Q(username=username)))

                if user.repositoryuser_set.filter(repo=repo).exists():
                    result['error'] = 'User has already access to this repository.'
                else:
                    result['username'] = user.username
                    result['id'] = user.pk
            except User.DoesNotExist:
                result['error'] = 'Username or e-mail address not found.'

            return HttpResponse(json.dumps(result), mimetype='application/json')

        repo_form = RepositoryForm(
            request.user, request.POST, instance=repo, prefix='repository')
        users_formset = RepositoryUserFormSet(request.POST, prefix='users')

        if repo_form.is_valid():
            repo_form.save()

            if users_formset.is_valid():
                for instance in users_formset.save(commit=False):
                    if not instance.pk:
                        instance.repo = repo
                    instance.save()

            messages.success(request, _('Repository updated.'))
            return redirect('accounts_profile')
    else:
        repo_form = RepositoryForm(request.user, instance=repo, prefix='repository')
        users_formset = RepositoryUserFormSet(
            prefix='users',
            queryset=repo.alterable_users
        )

    return render(request, 'repositories/manage_change.html', {
        'repo': repo,
        'form': repo_form,
        'users': users_formset,
    })


@login_required
def manage_add(request):
    if request.method == 'POST':
        form = RepositoryForm(request.user, request.POST)
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
            return redirect('accounts_profile')
    else:
        form = RepositoryForm(request.user)

    return render(request, 'repositories/manage_add.html', {
        'form': form,
    })


def overview(request):
    return render(request, 'repositories/overview.html', {
        'repository_list': Repository.objects.public_repositories(),
    })


@repository_view()
def summary(request, repo):
    return render(request, 'repositories/summary.html', {
        'repository': repo,
        'branches': repo.branches[:10],
        'tags': [tag for tag in repo.tags[:10] if tag.last_commit],
    })


@repository_view()
def heads(request, repo):
    return render(request, 'repositories/heads.html', {
        'repository': repo,
        'branches': repo.branches,
        'tags': repo.tags,
    })
