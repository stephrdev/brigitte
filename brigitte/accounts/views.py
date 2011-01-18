from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from brigitte.accounts.forms import RegistrationForm, FullProfileForm
from brigitte.accounts.forms import ChangeEmailForm
from brigitte.accounts.models import RegistrationProfile, EmailVerification

@login_required
def profile(request):
    return render(request, 'accounts/profile.html', {})

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
    verification = get_object_or_404(
        EmailVerification,
        token=token,
        code=code,
        user=request.user,
        is_expired=False
    )
    verification.is_approved = True
    verification.save()

    return redirect('accounts_profile')

