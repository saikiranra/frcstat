class ObjectShare:

    def __init__(self, objectInitFunc):
        self.objectInitFunc = objectInitFunc
        self._share = {}

    def get(self, *args, **kwargs):
        key = args, frozenset(kwargs.items())
        if key not in self._share:
            self._share[key] = self.objectInitFunc(*args, **kwargs)
        return self._share[key]
