
def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

class CaseInsensitiveDict(dict):

    """Basic case-insensitive dict with strings only keys."""

    proxy = {}

    def __init__(self, data=None):
        super().__init__()
        if data:
            self.proxy = dict((k.lower(), k) for k in data)
            for k in data:
                self[k] = data[k]
        else:
            self.proxy = dict()

    def __contains__(self, k):
        return k.lower() in self.proxy

    def __delitem__(self, k):
        key = self.proxy[k.lower()]
        super(CaseInsensitiveDict, self).__delitem__(key)
        del self.proxy[k.lower()]

    def __getitem__(self, k):
        key = self.proxy[k.lower()]
        return super(CaseInsensitiveDict, self).__getitem__(key)

    def get(self, k, default=None):
        return self[k] if k in self else default

    def __setitem__(self, k, v):
        super(CaseInsensitiveDict, self).__setitem__(k, v)
        self.proxy[k.lower()] = k

    @staticmethod
    def build(labels, data):
        row = CaseInsensitiveDict()
        for key, val in zip(labels, data):
            row[key] = val
        return row
