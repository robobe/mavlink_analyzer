

class EventHandler(object):
    def __init__(self):
        self.funcs = []

    

    def append(self, func):
        self.funcs.append(func)
        return self

    def remove(self, func):
        self.funcs.remove(func)
        return self

    def call(self, *args, **kwargs):
        for func in self.funcs:
            func(*args, **kwargs)

    __iadd__ = append
    __isub__ = remove
    __call__ = call