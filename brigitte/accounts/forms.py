from django import forms
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.contrib.sites.models import Site

from brigitte.accounts.models import Profile
from brigitte.accounts.models import EmailVerification, RegistrationProfile

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        exclude = ('user',)

class FullProfileForm(ProfileForm):
    first_name = forms.CharField(label=_('First name'), required=True)
    last_name = forms.CharField(label=_('Last name'), required=True)

    def __init__(self, *args, **kwargs):
        super(FullProfileForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = [
            'short_info',
            'first_name',
            'last_name',
        ]

    def save(self, *args, **kwargs):
        obj = super(FullProfileForm, self).save(*args, **kwargs)
        obj.user.first_name = self.cleaned_data['first_name']
        obj.user.last_name = self.cleaned_data['last_name']
        obj.user.save()

        return obj

class RegistrationForm(forms.Form):
    username = forms.CharField(label=_('Username'), required=True)

    email = forms.EmailField(label=_('E-Mail'))
    email_repeat = forms.EmailField(label=_('E-Mail (again)'), required=True)

    password = forms.CharField(label=_('Password'),
        widget=forms.PasswordInput(render_value=False))
    password_repeat = forms.CharField(label=_('Password (again)'),
        widget=forms.PasswordInput(render_value=False))

    first_name = forms.CharField(label=_('First name'), required=True)
    last_name = forms.CharField(label=_('Last name'), required=True)

    short_info = forms.CharField(label=_('Short info'), required=False,
        widget=forms.Textarea)

    def clean_username(self):
        if User.objects.filter(username__iexact=self.cleaned_data['username']):
            raise forms.ValidationError(
                _(u'This username is already in use. Please supply a different username.'))
        return self.cleaned_data['username']

    def clean_email(self):
        if User.objects.filter(email__iexact=self.cleaned_data['email']) or \
           EmailVerification.objects.filter(
               is_expired=False, new_email__iexact=self.cleaned_data['email']):
            raise forms.ValidationError(
                _(u'This email address is already in use. Please supply a different email address.'))
        return self.cleaned_data['email']

    def clean(self):
        if 'email' in self.cleaned_data and 'email_repeat' in self.cleaned_data:
            if self.cleaned_data['email'] != self.cleaned_data['email_repeat']:
                raise forms.ValidationError(_('The two email addresses do not match.'))

        if 'password' in self.cleaned_data and 'password_repeat' in self.cleaned_data:
            if self.cleaned_data['password'] != self.cleaned_data['password_repeat']:
                raise forms.ValidationError(_('You must type the same password each time.'))

        return self.cleaned_data

    def save(self, *args, **kwargs):
        new_user = RegistrationProfile.objects.create_inactive_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password'],
            email=self.cleaned_data['email'],
        )
        new_user.first_name = self.cleaned_data['first_name']
        new_user.last_name = self.cleaned_data['last_name']

        new_user.save()

        new_profile = Profile.objects.create(
            user=new_user,
            short_info=self.cleaned_data['short_info'],
        )
        new_profile.save()

        return new_user

class ChangeEmailForm(forms.Form):
    new_email = forms.EmailField(label=_('New E-Mail'), required=True)

    def clean_new_email(self):
        new_email = self.cleaned_data['new_email']

        user_emails = User.objects.filter(email=new_email).count()
        verification_emails = EmailVerification.objects.filter(
            new_email=new_email, is_expired=False).count()
        if user_emails + verification_emails > 0:
            raise forms.ValidationError(
                _(u'This email address is already in use. Please supply a different email address.'))

        return new_email

    def save(self, user=None):
        if not user:
            return None

        verification = EmailVerification.objects.create(
            user=user,
            old_email=user.email,
            new_email=self.cleaned_data['new_email']
        )

        data = {
            'user': user,
            'verification': verification,
            'site': Site.objects.get_current(),
        }

        subject = ''.join(render_to_string(
            'accounts/mails/emailverification_subject.html',
            data
        ).splitlines())
        body = render_to_string(
            'accounts/mails/emailverification.html', data)

        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [self.cleaned_data['new_email'],]
        )

        return verification

