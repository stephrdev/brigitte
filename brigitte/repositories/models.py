import os
from django.contrib.sites.models import Site
from datetime import datetime
from django.db import models
from django.db.models import Q
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

from brigitte.repositories.backends import get_backend

from brigitte.repositories.choices import REPO_TYPES, REPO_UPDATES

BRIGITTE_GIT_BASE_PATH = getattr(settings,
                                 'BRIGITTE_GIT_BASE_PATH',
                                 'git_repositories')

class RepositoryManager(models.Manager):
    def manageable_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            pk__in=user.repositoryuser_set.filter(can_admin=True).values_list('repo_id', flat=True)
        )

    def writeable_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            pk__in=user.repositoryuser_set.filter(can_write=True).values_list('repo_id', flat=True)
        )

    def public_repositories(self):
        return super(RepositoryManager, self).get_query_set().filter(private=False)

    def available_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            Q(
                Q(private=False)
                |
                Q(pk__in=user.repositoryuser_set.filter(can_read=True).values_list('repo_id', flat=True))
            )
        )

class Repository(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    slug = models.SlugField(_('Slug'), max_length=80, blank=False)
    title = models.CharField(_('Title'), max_length=80)
    description = models.TextField(_('Description'), blank=True)
    private = models.BooleanField(_('Private'), default=False)
    repo_type = models.CharField(_('Type'),
        max_length=4, choices=REPO_TYPES, default='git')

    objects = RepositoryManager()

    def __unicode__(self):
        return self.title

    @property
    def is_private_html(self):
        if self.private:
            return mark_safe('&#10004;')
        else:
            return mark_safe('&#10008;')

    @property
    def path(self):
        return os.path.join(
            BRIGITTE_GIT_BASE_PATH,
            self.user.username,
            '%s.git' % self.slug)

    @property
    def short_path(self):
        return '%s/%s.git' % (
            self.user.username,
            self.slug
        )

    @property
    def _repo(self):
        if not hasattr(self, '_repo_obj'):
            self._repo_obj = get_backend(self.repo_type)(self)
        return self._repo_obj

    def recent_commits(self, count=10):
        return self._repo.get_commits(count=count)

    @property
    def last_commit(self):
        if not hasattr(self, '_last_commit'):
            self._last_commit = self._repo.last_commit
        return self._last_commit

    @property
    def tags(self):
        if not hasattr(self, '_tags'):
            self._tags = self._repo.tags
        return self._tags

    @property
    def branches(self):
        if not hasattr(self, '_branches'):
            self._branches = self._repo.branches
        return self._branches

    @property
    def rw_url(self):
        if self.repo_type == 'git':
            return 'ssh://git@%s:%s/%s.git' % (Site.objects.get_current(), self.user.username, self.slug)

        return None

    @property
    def ro_url(self):
        if self.repo_type == 'git':
            return 'git://%s/%s/%s.git' % (Site.objects.get_current(), self.user.username, self.slug)

        return None

    def get_commit(self, sha):
        return self._repo.get_commit(sha)

    def get_commits(self, count=10, skip=0, head=None):
        return self._repo.get_commits(count=count, skip=skip, head=head)

    @property
    def alterable_users(self):
        return self.repositoryuser_set.exclude(user=self.user)

    def save(self, *args, **kwargs):
        if not self.pk:
            self._repo.init_repo()
        super(Repository, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._repo.delete_repo(self.slug)
        super(Repository, self).delete(*args, **kwargs)

    class Meta:
        unique_together = ('user', 'slug')
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')

class RepositoryUser(models.Model):
    repo = models.ForeignKey(Repository, verbose_name=_('Repository'))
    user = models.ForeignKey(User, verbose_name=_('User'))

    can_read = models.BooleanField(_('Can read'), default=True)
    can_write = models.BooleanField(_('Can write'), default=False)
    can_admin = models.BooleanField(_('Can admin'), default=False)

    def __unicode__(self):
        return '%s/%s (%s, %s, %s)' % (
            self.repo,
            self.user,
            self.can_read,
            self.can_write,
            self.can_admin
        )

    def save(self, *args, **kwargs):
        if self.can_admin:
            self.can_write = True
            self.can_read = True
        elif self.can_write:
            self.can_read = True

        super(RepositoryUser, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('repo', 'user')
        verbose_name = _('Repository user')
        verbose_name_plural = _('Repository users')

class RepositoryUpdateManager(models.Manager):
    def pending_updates(self, user):
        return super(RepositoryUpdateManager, self).get_query_set().filter(
            is_exported=False
        )

class RepositoryUpdate(models.Model):
    repo = models.ForeignKey(Repository, verbose_name=_('Repository'))
    user = models.ForeignKey(User, verbose_name=_('User'))
    repo_type = models.CharField(_('Type'), max_length=4, choices=REPO_TYPES)
    update = models.CharField(_('Update'), max_length=64, choices=REPO_UPDATES)

    updated = models.DateTimeField(_('Updated'), default=datetime.now)

    is_exported = models.BooleanField(_('Is exported'), default=False)
    exported = models.DateTimeField(_('Exported'), blank=True, null=True)

    objects = RepositoryUpdateManager()

    def __unicode__(self):
        return '%s/%s %s: %s' % (self.repo,
                                 self.user,
                                 self.updated,
                                 self.update)

    def save(self, *args, **kwargs):
        if self.is_exported and not self.exported:
            self.exported = datetime.now()
        super(RepositoryUpdate, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _('Repository update')
        verbose_name_plural = _('Repository updates')

