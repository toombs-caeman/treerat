import functools
class Evaluator:
    def __init__(self):
        self.nodes = {}

    def node(self, name, f=None, /):
        if f is None:
            if callable(name):
                name, f = name.__name__, name
            else:
                return functools.partial(self.node, name)
        self.nodes[name] = f
        return f

    def __call__(self, ast):
        match ast:
            case [f, *args]:
                return self.nodes[f](*args)
            case _:
                raise ValueError('runtime error invalid ast:', repr(ast))


