# -*- coding: utf-8 -*-
REPO_BACKENDS = {}

class RepositoryTypeNotAvailable(Exception): pass

try:
    from brigitte.repositories.backends import libgit
    REPO_BACKENDS['git'] = libgit.Repo
except ImportError:
    from brigitte.repositories.backends import git
    REPO_BACKENDS['git'] = git.Repo

try:
    from brigitte.repositories.backends import hg
    REPO_BACKENDS['hg'] = hg.Repo
except ImportError:
    pass

def get_backend(repo_type):
    if not repo_type in REPO_BACKENDS:
        raise RepositoryTypeNotAvailable(repo_type)

    return REPO_BACKENDS[repo_type]
