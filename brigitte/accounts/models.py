# -*- coding: utf-8 -*-
from django.db import models
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _


class Profile(models.Model):
    user = models.OneToOneField(User, unique=True)
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


class SshPublicKey(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'), blank=False)
    description = models.CharField(_('Description'), max_length=250, blank=True)
    can_read = models.BooleanField(_('Can read'), default=True)
    can_write = models.BooleanField(_('Can write'), default=False)
    key = models.TextField(_('Key'), blank=False)

    def __unicode__(self):
        if self.description:
            return self.description
        else:
            return self.short_key

    @property
    def short_key(self):
        return self.key[:32] + '...'

    @property
    def can_read_html(self):
        if self.can_read:
            return mark_safe('&#10004;')
        else:
            return mark_safe('&#10008;')

    @property
    def can_write_html(self):
        if self.can_write:
            return mark_safe('&#10004;')
        else:
            return mark_safe('&#10008;')

    class Meta:
        verbose_name = _('SSH Public Key')
        verbose_name_plural = _('SSH Public Keys')
