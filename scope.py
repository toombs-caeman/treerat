"""
generic implementations of name resolution
"""
class scope:
    def __init__(self, parent:scope|None=None, initial:dict|None=None):
        self.dict = {} if initial is None else initial.copy()
        self.parent = parent
        self.globals = self if parent is None else parent.globals
    def __getitem__(self, key:str):
        if key in self.dict:
            return self.dict[key]
        if self.parent is not None:
            return self.parent[key]
        raise NameError(key)
    def __setitem__(self, key:str, value):
        self.dict[key] = value
    def __delitem__(self, key:str):
        del self.dict[key]
    def __contains__(self, key:str):
        if self.parent is None:
            return key in self.dict
        return key in self.dict or key in self.parent
    def hoist(self, key:str, levels=1):
        v = self[key]
        del self[key]
        scope = self
        while scope is not None and levels:
            scope = scope.parent
            levels -= 1
        if scope is None:
            raise ValueError('scope stack not that deep')
        scope[key] = v

    def __enter__(self):
        return scope(self)

    def __exit__(self, *_):
        return False
