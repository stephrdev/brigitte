from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User

from brigitte.repositories.backends.git import Repo

class Repository(models.Model):
    user = models.ForeignKey(User, verbose_name=_('User'))
    path = models.CharField(_('Repository Path'), max_length=255)
    title = models.CharField(_('Title'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, blank=False)
    description = models.TextField(_('Description'), blank=True)

    def __unicode__(self):
        return self.title

    @property
    def _repo(self):
        if not hasattr(self, '_repo_obj'):
            self._repo_obj = Repo(self.path)
        return self._repo_obj

    @property
    def recent_commits(self):
        return self._repo.get_recent_commits(None, 10)

    @property
    def last_commit(self):
        return self._repo.get_last_commit()

    def get_commit(self, sha):
        return self._repo.get_commit(sha)

    class Meta:
        unique_together = ('user', 'slug')
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')
