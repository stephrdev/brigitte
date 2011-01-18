from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django.utils.hashcompat import sha_constructor

from datetime import datetime, timedelta
from uuid import uuid4
import random
import re

from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.core.mail import send_mail

SHA1_RE = re.compile('^[a-f0-9]{40}$')

def generate_token():
    return str(uuid4())

def gen_confirm_expire_date():
    return datetime.now() + timedelta(days=2)

class Profile(models.Model):
    user = models.OneToOneField(User, verbose_name=_('User'), unique=True,
                             blank=False)
    short_info = models.TextField(_('Short info'), blank=True)

    def __unicode__(self):
        return '%s %s' % (self.user.first_name, self.user.last_name)

    @property
    def first_name(self):
        return self.user.first_name

    @property
    def last_name(self):
        return self.user.last_name

    class Meta:
        verbose_name = _('Profile')
        verbose_name_plural = _('Profiles')

class RegistrationManager(models.Manager):
    def activate_user(self, activation_key):
        if SHA1_RE.search(activation_key):
            try:
                profile = self.get(activation_key=activation_key)
            except self.model.DoesNotExist:
                return False
            if not profile.activation_key_expired():
                user = profile.user
                user.is_active = True
                user.save()
                profile.activation_key = self.model.ACTIVATED
                profile.save()
                return user
        return False

    def create_inactive_user(self, username, password, email):
        new_user = User.objects.create_user(username, email, password)
        new_user.is_active = False
        new_user.save()

        registration_profile = self.create_profile(new_user)

        current_site = Site.objects.get_current()

        subject = ''.join(render_to_string(
            'accounts/mails/activation_email_subject.html',
            {'site': current_site }
        ).splitlines())

        message = render_to_string(
            'accounts/mails/activation_email.html',
            {
                'activation_key': registration_profile.activation_key,
                'expiration_days': settings.ACCOUNT_ACTIVATION_DAYS,
                'site': current_site
            }
        )

        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [new_user.email])
        return new_user

    def create_profile(self, user):
        salt = sha_constructor(str(random.random())).hexdigest()[:5]
        activation_key = sha_constructor(salt+user.username).hexdigest()
        return self.create(user=user,
                           activation_key=activation_key)

    def delete_expired_users(self):
        for profile in self.all():
            if profile.activation_key_expired():
                user = profile.user
                if not user.is_active:
                    user.delete()

class RegistrationProfile(models.Model):
    ACTIVATED = 'ALREADY_ACTIVATED'

    user = models.ForeignKey(User, unique=True, verbose_name=_('User'))
    activation_key = models.CharField(_('Activation key'), max_length=40)

    objects = RegistrationManager()

    class Meta:
        verbose_name = _('Registration profile')
        verbose_name_plural = _('Registration profiles')

    def __unicode__(self):
        return u'Registration information for %s' % self.user

    def activation_key_expired(self):
        expiration_date = timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS)
        return self.activation_key == self.ACTIVATED or \
               (self.user.date_joined + expiration_date <= datetime.now())
    activation_key_expired.boolean = True

class EmailVerification(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'), blank=False)
    old_email = models.EmailField(_('Old E-Mail'))
    new_email = models.EmailField(_('New E-Mail'))
    token = models.CharField(_('Request Token'), max_length=40,
                             default=generate_token)
    code = models.CharField(_('Request Code'), max_length=40,
                            default=generate_token)
    is_approved = models.BooleanField(_('Is approved'), default=False)
    is_expired = models.BooleanField(_('Is expired'), default=False)
    expiration_date = models.DateTimeField(_('Expiration date'),
                                           default=gen_confirm_expire_date)

    def __unicode__(self):
        return '%s - %s/%s' % (self.user, self.old_email, self.new_email)

    def save(self, *args, **kwargs):
        if self.is_approved:
            EmailVerification.objects.filter(
                user=self.user, is_approved=False).update(is_expired=True)
            self.is_expired = True
            if self.user.email == self.old_email:
                self.user.email = self.new_email
                self.user.save()
        return super(EmailVerification, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('E-Mail Verification')
        verbose_name_plural = _('E-Mail Verifications')

