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

    def __init__(self, path):
        self.path = path

class BaseTag:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE)
        output = raw.communicate()[0]
        return output

    path = None

    def __init__(self, path, name):
        self.path = path
        self.name = name

class BaseBranch:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE)
        output = raw.communicate()[0]
        return output

    path = None

    def __init__(self, path, name, is_master):
        self.path = path
        self.name = name
        self.is_master = is_master

class BaseCommit:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE, stderr=PIPE)
        output, err = raw.communicate()
        if err:
            raise ShellCommandException(err)
        return output

    path = None

    def __init__(self, path, inp):
        self.path = path
        self.__dict__.update(**dict([(str(k), v) for k,v in inp.items()]))

