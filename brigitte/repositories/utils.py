import os
import pygments
import pygments.lexers as lexers
import pygments.formatters as formatters
from pygments.util import ClassNotFound
from django.utils.safestring import mark_safe
from django.conf import settings

from brigitte.repositories.gitolite import generate_gitolite_conf
from brigitte.repositories.gitolite import export_public_keys
from brigitte.repositories.gitolite import update_gitolite_repo

from brigitte.repositories.models import Repository, RepositoryUpdate
from brigitte.repositories.choices import REPO_UPDATES_DICT
from brigitte.repositories.tasks import UpdateGitoliteTask

class NakedHtmlFormatter(formatters.HtmlFormatter):
    def wrap(self, source, outfile):
        return self._wrap_code(source)
    def _wrap_code(self, source):
        for i, t in source:
            yield i, t

def unescape_amp(text):
    return text.replace('&amp;', '&')

def pygmentize(mime, blob):
    try:
        lexer = lexers.get_lexer_for_mimetype(mime)
    except ClassNotFound:
        try:
            lexer = lexers.get_lexer_by_name(mime)
        except:
            lexer = lexers.get_lexer_by_name('text')

    pygmented_string = pygments.highlight(blob, lexer, NakedHtmlFormatter())
    pygmented_string = unescape_amp(pygmented_string)

    return mark_safe(pygmented_string)

def build_path_breadcrumb(path):
    if not path:
        return []
    links = []
    cur_path = None
    for part in path.split('/'):
        if cur_path:
            cur_path += '/' +part
        else:
            cur_path = part
        links.append({
            'path': cur_path,
            'name': part,
        })
    return links

def register_repository_update(user, change, repo=None):
    assert REPO_UPDATES_DICT.has_key(change), 'Invalid update type'

    if repo:
        RepositoryUpdate.objects.create(
            user=user,
            repo=repo,
            repo_type='git',
            update=change,
        )
    else:
        for repo in Repository.objects.writeable_repositories(user):
            RepositoryUpdate.objects.create(
                user=user,
                repo=repo,
                repo_type='git',
                update=change,
            )

    UpdateGitoliteTask.delay()

def update_gitolite():
    BRIGITTE_GIT_ADMIN_PATH = getattr(settings,
                                     'BRIGITTE_GIT_ADMIN_PATH',
                                      'gitolite-admin')

    generate_gitolite_conf(os.path.join(BRIGITTE_GIT_ADMIN_PATH,
                                        'conf/gitolite.conf'))

    export_public_keys(os.path.join(BRIGITTE_GIT_ADMIN_PATH, 'keydir'))

    update_gitolite_repo(BRIGITTE_GIT_ADMIN_PATH)

