# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from brigitte.accounts.forms import SshPublicKeyForm
from brigitte.accounts.models import SshPublicKey
from brigitte.repositories.models import Repository


@login_required
def profile(request):
    public_repositories = []
    private_repositories = []
    for repo in Repository.objects.dashboard_available_repositories(request.user):
        if repo.repositoryuser_set.filter(user=request.user, can_write=True).exists():
            repo.can_write = mark_safe('&#10004;')
        else:
            repo.can_write = mark_safe('&#10005;')

        if repo.repositoryuser_set.filter(user=request.user, can_admin=True).exists():
            repo.can_admin = True
        else:
            repo.can_admin = False

        if repo.private:
            private_repositories.append(repo)
        else:
            public_repositories.append(repo)

    return render(request, 'accounts/profile.html', {
        'private_repository_list': private_repositories,
        'public_repository_list': public_repositories,
    })


def public_profile(request, user):
    user = get_object_or_404(User, username=user)
    return render(request, 'accounts/public_profile.html', {
        'user': user,
        'repository_list': user.repository_set.user_public_repositories(user),
    })


@login_required
def keys_list(request):
    return render(request, 'accounts/keys_list.html', {
        'keys': request.user.sshpublickey_set.all(),
    })


@login_required
def keys_add(request):
    if request.method == 'POST':
        form = SshPublicKeyForm(request.POST)
        if form.is_valid():
            key = form.save(commit=False)
            key.user = request.user
            key.save()
            messages.success(request, _('Key added.'))
            return redirect('accounts_keys_list')
    else:
        form = SshPublicKeyForm()

    return render(request, 'accounts/keys_change.html', {'form': form})


@login_required
def keys_change(request, pk):
    key = get_object_or_404(SshPublicKey, pk=pk, user=request.user)

    if request.method == 'POST':
        form = SshPublicKeyForm(request.POST, instance=key)
        if form.is_valid():
            key = form.save()
            messages.success(request, _('Key updated.'))
            return redirect('accounts_keys_list')
    else:
        form = SshPublicKeyForm(instance=key)

    return render(request, 'accounts/keys_change.html', {'form': form, 'key': key})


@login_required
def keys_delete(request, pk):
    try:
        key = SshPublicKey.objects.get(pk=pk, user=request.user)
        key.delete()
        messages.success(request, _('Key deleted.'))
        return redirect('accounts_keys_list')
    except SshPublicKey.DoesNotExist:
        messages.error(request, _('Key not found.'))
        return redirect('accounts_keys_list')
