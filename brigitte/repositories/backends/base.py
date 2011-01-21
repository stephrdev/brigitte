from subprocess import Popen, PIPE

class BaseRepo:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE)
        output = raw.communicate()[0]
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

class BaseCommit:
    def syswrapper(self, cmd):
        raw = Popen(cmd, stdout=PIPE)
        output = raw.communicate()[0]
        return output

    path = None

    def __init__(self, path, inp):
        self.path = path
        self.__dict__.update(**dict([(str(k), v) for k,v in inp.items()]))

