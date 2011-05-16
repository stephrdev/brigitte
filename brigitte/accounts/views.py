from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from django.utils.safestring import mark_safe

from brigitte.accounts.forms import RegistrationForm, FullProfileForm
from brigitte.accounts.forms import ChangeEmailForm, SshPublicKeyForm
from brigitte.accounts.models import RegistrationProfile, EmailVerification
from brigitte.accounts.models import SshPublicKey

from brigitte.repositories.models import Repository
from brigitte.repositories.utils import register_repository_update

@login_required
def profile(request):
    public_repositories = []
    private_repositories = []
    for repo in Repository.objects.dashboard_available_repositories(request.user):
        if repo.repositoryuser_set.filter(user=request.user, can_write=True).exists():
            repo.can_write = mark_safe('&#10004;')
        else:
            repo.can_write = mark_safe('&#10005;')

        if repo.private:
            private_repositories.append(repo)
        else:
            public_repositories.append(repo)

    return render(request, 'accounts/profile.html', {
        'private_repository_list': private_repositories,
        'public_repository_list': public_repositories,
    })

def registration_activate(request, activation_key):
    activation_key = activation_key.lower()
    account = RegistrationProfile.objects.activate_user(activation_key)
    return render(request, 'accounts/registration_activate.html', {
        'account': account,
        'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
    })

def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_user = form.save()
            return redirect('registration_complete')
    else:
        form = RegistrationForm()

    return render(request, 'accounts/registration.html', {
        'form': form
    })

def registration_complete(request):
    return render(request, 'accounts/registration_complete.html', {
        'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS
    })

@login_required
def profile_change(request):
    if request.method == 'POST':
        form = FullProfileForm(request.POST, instance=request.user.get_profile())
        if form.is_valid():
            profile = form.save()
            messages.success(request, _('Profile updated.'))
            return redirect('accounts_profile_change')
    else:
        form = FullProfileForm(instance=request.user.get_profile(),
                               initial={'first_name': request.user.first_name,
                                        'last_name': request.user.last_name})

    return render(request, 'accounts/profile_change.html', {'form': form})

@login_required
def email_change(request):
    if request.method == 'POST':
        form = ChangeEmailForm(request.POST)
        if form.is_valid():
            verification = form.save(request.user)
            return redirect('accounts_email_change_requested')
    else:
        form = ChangeEmailForm()

    return render(request, 'accounts/email_change.html', {'form': form})

@login_required
def email_change_requested(request):
    return render(request, 'accounts/email_change_requested.html', {})

@login_required
def email_change_approve(request, token, code):
    try:
        verification = EmailVerification.objects.get(
            token=token,
            code=code,
            user=request.user,
            is_expired=False
        )
        verification.is_approved = True
        verification.save()
        messages.success(request, _('E-Mail changed to %s') % verification.new_email)
    except EmailVerification.DoesNotExist:
        messages.error(request, _('E-Mail could not be changed. Invalid link.'))

    return redirect('accounts_profile')

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
            register_repository_update(key.user, 'key_added')
            messages.success(request, _('Key added.'))
            return redirect('accounts_keys_list')
    else:
        form = SshPublicKeyForm()

    return render(request, 'accounts/keys_add.html', {'form': form})

@login_required
def keys_change(request, pk):
    key = get_object_or_404(SshPublicKey, pk=pk, user=request.user)

    if request.method == 'POST':
        form = SshPublicKeyForm(request.POST, instance=key)
        if form.is_valid():
            key = form.save()
            register_repository_update(key.user, 'key_changed')
            messages.success(request, _('Key updated.'))
            return redirect('accounts_keys_list')
    else:
        form = SshPublicKeyForm(instance=key)

    return render(request, 'accounts/keys_change.html', {'form': form})

@login_required
def keys_delete(request, pk):
    try:
        key = SshPublicKey.objects.get(pk=pk, user=request.user)
        key.delete()
        register_repository_update(request.user, 'key_deleted')
        messages.success(request, _('Key deleted.'))
        return redirect('accounts_keys_list')
    except SshPublicKey.DoesNotExist:
        messages.error(request, _('Key not found.'))
        return redirect('accounts_keys_list')

