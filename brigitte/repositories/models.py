import os
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from brigitte.repositories.backends.git import Repo

BRIGITTE_GIT_BASE_PATH = getattr(settings,
                                 'BRIGITTE_GIT_BASE_PATH',
                                 'git_repositories')

class RepositoryManager(models.Manager):
    def manageable_repositories(self, user):
        return [ru.repo for ru in user.repositoryuser_set.filter(
            can_admin=True)]

class Repository(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    slug = models.SlugField(_('Slug'), max_length=255, blank=False)
    title = models.CharField(_('Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True)

    objects = RepositoryManager()

    def __unicode__(self):
        return self.title

    @property
    def path(self):
        return os.path.join(
            BRIGITTE_GIT_BASE_PATH,
            self.user.username,
            '%s.git' % self.slug)

    @property
    def _repo(self):
        if not hasattr(self, '_repo_obj'):
            self._repo_obj = Repo(self.path)
        return self._repo_obj

    def recent_commits(self, count=10):
        return self._repo.get_recent_commits(None, count)

    @property
    def last_commit(self):
        return self._repo.get_last_commit()

    @property
    def get_tags(self):
        return self._repo.get_tags()

    def get_commit(self, sha):
        return self._repo.get_commit(sha)

    def user_is_admin(self, user):
        return self.repositoryuser_set.filter(
            user=user,
            can_admin=True
        ).exists()

    @property
    def alterable_users(self):
        return self.repositoryuser_set.exclude(user=self.user)

    def save(self, *args, **kwargs):
        if not self.pk:
            self._repo.init_repo()
        super(Repository, self).save(*args, **kwargs)

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

