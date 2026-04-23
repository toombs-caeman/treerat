"""
defines multiset better than collections.Counter I think
something to combine with graph maybe.
"""
class multiset[_KT](dict):
    def __init__(self, iterable):
        if isinstance(iterable, set):
            return super().__init__((k, 1) for k in iterable)
        return super().__init__(iterable)
    def __getitem__(self, key:_KT) -> int:
        return self.get(key, 0)
    def add(self, k:_KT):
        self[k] += 1
    def remove(self, k:_KT, count=1):
        if k in self:
            self[k] = max(0, self[k] - count)
    def __or__(self, other):
        match other:
            case multiset():
                return multiset(
                    (k, self[k] + other[k])
                    for k in self.keys() | other.keys()
                )
            case set():
                copy = multiset(self)
                for k in other:
                    copy.add(k)
                return copy
            case _:
                return NotImplemented
    def __ror__(self, other):
        return self | other
    def __sub__(self, other):
        match other:
            case multiset():
                copy = multiset(self)
                for k, v in other.items():
                    copy[k] = max(0, copy[k] - v)
                return copy
            case set():
                copy = multiset(self)
                for k in other:
                    copy.add(k)
                return copy
            case _:
                return NotImplemented

