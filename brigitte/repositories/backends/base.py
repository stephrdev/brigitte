from subprocess import Popen, PIPE

class ShellCommandException(Exception): pass

class BaseRepo:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE, stderr=PIPE)
        output, err = raw.communicate()
        if err:
            raise ShellCommandException(err)
        return output

    path = None

    def __init__(self, repo):
        self.repo = repo

    @property
    def path(self):
        return self.repo.path

class BaseTag:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE)
        output = raw.communicate()[0]
        return output

    repo = None

    def __init__(self, repo, name):
        self.repo = repo
        self.name = name

class BaseBranch:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE)
        output = raw.communicate()[0]
        return output

    repo = None

    def __init__(self, repo, name, is_master):
        self.repo = repo
        self.name = name
        self.is_master = is_master

class BaseCommit:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE, stderr=PIPE)
        output, err = raw.communicate()
        if err:
            raise ShellCommandException(err)
        return output

    repo = None

    def __init__(self, repo, inp):
        self.repo = repo
        self.__dict__.update(**dict([(str(k), v) for k,v in inp.items()]))

