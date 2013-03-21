# -*- coding: utf-8 -*-
REPO_BACKENDS = {}
REPO_TYPES = []


class RepositoryTypeNotAvailable(Exception):
    pass


try:
    from brigitte.backends import libgit
    REPO_BACKENDS['git'] = libgit.Repo
    REPO_TYPES.append(('git', 'GIT'))
except ImportError:
    from brigitte.backends import git
    REPO_BACKENDS['git'] = git.Repo
    REPO_TYPES.append(('git', 'GIT'))


try:
    from brigitte.backends import hg
    REPO_BACKENDS['hg'] = hg.Repo
    REPO_TYPES.append(('hg', 'Mercurial'))
except ImportError:
    pass


def get_backend(repo_type):
    if not repo_type in REPO_BACKENDS:
        raise RepositoryTypeNotAvailable(repo_type)

    return REPO_BACKENDS[repo_type]
