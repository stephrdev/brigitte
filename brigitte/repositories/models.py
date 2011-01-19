from django.db import models
from django.utils.translation import ugettext_lazy as _
from brigitte.Git import Repo


class Repository(models.Model):
    path = models.CharField(_('Repository Path'), max_length=255)
    title = models.CharField(_('Title'), max_length=255)
    slug = models.SlugField(_('Slug'), max_length=255, blank=False, unique=True)
    description = models.TextField(_('Description'), blank=True)

    def __unicode__(self):
        return self.title

    @property
    def recent_commits(self):
        return Repo(self.path).recent_commits(None, 10)

    @property
    def last_commit(self):
        return Repo(self.path).recent_commits(None, 1)[0]

    class Meta:
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')