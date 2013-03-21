# -*- coding: utf-8 -*-
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe

from brigitte.backends import get_backend
from brigitte.backends import REPO_TYPES


BRIGITTE_GIT_BASE_PATH = getattr(settings, 'BRIGITTE_GIT_BASE_PATH',
    os.path.join(settings.PROJECT_ROOT, 'git_repositories'))


class RepositoryManager(models.Manager):
    def manageable_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            pk__in=user.repositoryuser_set.filter(
                can_admin=True).order_by('-last_commit_date').values_list('repo_id', flat=True)
        )

    def writeable_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            pk__in=user.repositoryuser_set.filter(
                can_write=True).order_by('-last_commit_date').values_list('repo_id', flat=True)
        )

    def public_repositories(self):
        return super(RepositoryManager, self).get_query_set().filter(
            private=False).order_by('-last_commit_date')

    def user_public_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            private=False, user=user).order_by('-last_commit_date')

    def available_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            Q(
                Q(private=False)
                |
                Q(pk__in=user.repositoryuser_set.filter(
                    can_read=True).values_list('repo_id', flat=True))
            )
        ).order_by('-last_commit_date')

    def dashboard_available_repositories(self, user):
        return super(RepositoryManager, self).get_query_set().filter(
            Q(
                Q(private=False, pk__in=user.repositoryuser_set.filter(
                    can_read=True))
                |
                Q(pk__in=user.repositoryuser_set.filter(
                    can_read=True).values_list('repo_id', flat=True))
            )
        ).order_by('-last_commit_date')


class Repository(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    slug = models.SlugField(_('Slug'), max_length=80, blank=False)
    title = models.CharField(_('Title'), max_length=80)
    description = models.TextField(_('Description'), blank=True)
    private = models.BooleanField(_('Private'), default=False)
    repo_type = models.CharField(_('Type'), max_length=4, choices=REPO_TYPES,
        default='git')
    last_commit_date = models.DateTimeField(blank=True, null=True)

    objects = RepositoryManager()

    def __unicode__(self):
        return self.title

    def get_last_commit(self):
        # TODO: cache self.last_commit with git hook ...
        last_commit = self.last_commit
        if not self.last_commit_date and last_commit:
            self.last_commit_date = last_commit.commit_date
            self.save()
        elif self.last_commit_date and last_commit and self.last_commit_date != last_commit.commit_date:
            self.last_commit_date = self.last_commit.commit_date
            self.save()
        return last_commit

    @property
    def private_html(self):
        if self.private:
            return mark_safe('&#10004;')
        else:
            return mark_safe('&#10008;')

    @property
    def path(self):
        if self.repo_type == 'git':
            return os.path.join(BRIGITTE_GIT_BASE_PATH, self.user.username,
                '%s.git' % self.slug)

        return None

    @property
    def short_path(self):
        if self.repo_type == 'git':
            return '%s/%s.git' % (self.user.username, self.slug)

        return None

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
            return 'git@%s:%s' % (
                Site.objects.get_current(), self.short_path)

        return None

    @property
    def ro_url(self):
        if self.repo_type == 'git':
            return 'git://%s/%s' % (Site.objects.get_current(), self.short_path)

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
        self._repo.repo_settings_changed()
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
