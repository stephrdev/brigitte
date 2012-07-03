# -*- coding: utf-8 -*-
from subprocess import Popen, PIPE


class ShellCommandException(Exception):
    pass

class ShellMixin(object):
    def exec_command(self, command):
        if not isinstance(command, (list, tuple)):
            cmd = command.split(' ')
        else:
            cmd = command

        raw = Popen(cmd, stdout=PIPE, stderr=PIPE)
        output, err = raw.communicate()
        if err:
            raise ShellCommandException(err)
        return output

    def exec_command_strip(self, command):
        return self.exec_command(command).strip()

class BaseRepo(ShellMixin):
    """ Base Repo class to inherit from. """
    repo = None

    def __init__(self, repo):
        """ repo should be a model instance of Repository """
        self.repo = repo

    def __repr__(self):
        return u'<Repo: %s>' % self.path

    @property
    def path(self):
        """ This property should return the full repository path. """
        return self.repo.path

    @property
    def tags(self):
        """ This property should return a list of Tag objects """
        raise NotImplementedError

    @property
    def branches(self):
        """ This property should return a list of Branch objects """
        raise NotImplementedError

    @property
    def last_commit(self):
        """
        This property should return a Commit object with the last commit
        from repository.
        """
        raise NotImplementedError

    def get_commits(self, count, skip, head):
        """
        This method should return a list of Commit objects.
        - count is the amount of commits to return.
        - skip is the amount of commits to skip on return.
        - head defines the branch/tag for the commit list.
        """
        raise NotImplementedError

    def get_commit(self, sha):
        """ This method returns a single Commit object for a given sha """
        raise NotImplementedError

    def init_repo(self):
        """ This method should initialize the repository """
        raise NotImplementedError

    def delete_repo(self):
        """ This method should delete the repository """
        raise NotImplementedError

class BaseCommit(ShellMixin):
    """ Base Commit class to inherit from. """

    # some basic attributes. These attributes are needed.
    id = None
    tree = None
    parents = []

    message = None
    short_message = None

    author = None
    author_email = None
    committer = None
    commiter_email = None

    commit_date = None

    repo = None

    def __init__(self, repo, params):
        self.repo = repo
        self.__dict__.update(**dict([(str(k), v) for k,v in params.items()]))

    def __repr__(self):
        return u'<Commit: %s>' % self.id

    @property
    def short_id(self):
        return (self.id or '')[:7]

    @property
    def short_tree(self):
        return (self.id or '')[:7]

    @property
    def short_parents(self):
        return [parent[:7] for parent in self.parents]

    def get_archive(self):
        """
        This method should return a dict containing a filename, mimetype and
        a StringIO. Example:
        {
            'filename': 'myfilename.zip',
            'mime': 'application/zip',
            'data': StringIO(),
        }
        """
        raise NotImplementedError

    def get_tree(self, path):
        """ This method should return a Tree object for the given path. """
        raise NotImplementedError

    def get_file(self, path):
        """ This method should return a File object for the given path. """
        raise NotImplementedError

    @property
    def changed_files(self):
        """
        This method should return a list of dicts with all changed files.
        Example:
        [
            {'file': 'myfile.py', 'lines_added': 1, 'lines_removed': 2},
            {'file': 'myfile2.py', 'lines_added': 1, 'lines_removed': 2}
        ]
        """
        raise NotImplementedError

    @property
    def commit_diff(self):
        """ This property should return the full commit diff. """
        raise NotImplementedError

    @property
    def file_diffs(self):
        """
        This property should return a list of changed files including
        file diff and combined line numbers. Example:
        [
            {'file': 'myfile.py', 'lines_added': 1, 'lines_removed': 2
             'line_numbers': [], 'diff': '....................'},
            {'file': 'myfile2.py', 'lines_added': 1, 'lines_removed': 2
             'line_numbers': [], 'diff': '....................'},
        ]
        """
        raise NotImplementedError

    def get_file_diff(self, path):
        """
        This method should return a dict with path, combined line numbers
        and a diff. Example:
        {'file': 'myfile.py', 'line_numbers': [], 'diff': '............'}
        """
        raise NotImplementedError

class BaseTag(ShellMixin):
    repo = None
    name = None
    id = None

    def __init__(self, repo, name, id):
        self.repo = repo
        self.name = name
        self.id = id

    def __repr__(self):
        return u'<Tag: %s>' % self.name

    @property
    def last_commit(self):
        """ This property should return the last commit of this tag. """
        raise NotImplementedError

class BaseBranch(ShellMixin):
    repo = None
    name = None
    id = None
    is_master = False

    def __init__(self, repo, name, id, is_master=False):
        self.repo = repo
        self.name = name
        self.id = id
        self.is_master = is_master

    def __repr__(self):
        return u'<Branch: %s>' % self.name

    @property
    def last_commit(self):
        """ This property should return the last commit of this branch. """
        raise NotImplementedError

class BaseTree:
    repo = None
    path = None
    tree = None

    def __init__(self, repo, path, tree):
        self.repo = repo
        self.path = path
        self.tree = tree

    def __repr__(self):
        return u'<Tree: %s>' % self.path

class BaseFile:
    repo = None
    path = None
    size = None
    date = None
    content = None

    def __init__(self, repo, path, content, size, date):
        self.repo = repo
        self.path = path
        self.content = content
        self.size = size
        self.date = date

    def __repr__(self):
        return u'<File: %s>' % self.path
