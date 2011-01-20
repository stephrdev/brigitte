class BaseRepo:
    path = None

    def __init__(self, path):
        self.path = path

class BaseCommit:
    path = None

    def __init__(self, path, inp):
        self.path = path
        self.__dict__.update(**dict([(str(k), v) for k,v in inp.items()]))

