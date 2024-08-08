from base import *
import abc








class Graph(Evaluator):
    """
    Each method receives evaluated arguments and should return zero or more effects.

    Some nodes need special loading proceedures.
    A node 'Foo' will be loaded by method '_load__Foo' if it is defined.
    """
    # sets of nodes which must have a total ordering relative to each member of the set
    total_order = (
            ('Input', 'Print'), # terminal input and output need to be ordered together
            )
    def __init__(self):
        self._namespace = namespace()
        self._model = standard.Graph()
        self._total_order:dict[tuple,tuple|None] = {s:None for s in self.total_order}

    @abc.abstractmethod
    def __call__(self, ast):
        self._load(ast)
        for op, *args in self._model.order:
            effects = getattr(self, op)(*args)
            if not effects:
                continue
            for k,v in effects.items():
                pass

    def _load(self, ast):
        if isinstance(ast, str):
            return ast
        op, *args = ast

        # check if there is special loading needed.
        if hasattr(self, (loader:=f'_load__{op}')):
            return getattr(self, loader)(*args)

        if not hasattr(self, op):
            raise EvalError(f'unrecognized ast type {op}: {ast!r}')
        args = tuple(self._load(a) for a in args)
        node = (op, *args)
        deps = [a for a in args if isinstance(a, int)]
        for s in self._total_order:
            if op in s:
                if (last:=self._total_order[s]) is not None:
                    deps.append(last)
                    self._total_order[s] = node
        return self._model.node(node, *deps)


    def _load__Var(self, name):
        return self._namespace[name]

    def _load__Scope(self, *stmts):
        v = None
        with self._namespace:
            for stmt in stmts:
                v = self._load(stmt)
        return v
    def Print(self, expr):
        print(expr)
    def Input(self, prompt):
        return input(prompt)





