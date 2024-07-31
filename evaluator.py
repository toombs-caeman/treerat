from abc import ABC, abstractmethod

class Evaluator(ABC):
    """
    Base class for evaluators.

    In general an evaluator embodies the semantics of a language.
    Each evaluator receives an AST and does the computation represented by the AST.
    Subclasses of Evaluator should implement the __call__() method to do this.

    As a general pattern (not all evaluators have to do this), each recognized type of node
    should have a corresponding method in the evaluator to implement the semantics of that node.
    This makes it relatively straightforward to extend an Evaluator through subclassing.

    Evaluators should raise a RuntimeError if the ast they receive is invalid.
    """
    @abstractmethod
    def __call__(self, ast):
        pass

class RuntimeError(Exception):
    """The evaluator had a problem."""

class TreeWalk(Evaluator):
    """
    A base class for tree walk evaluators.
    Each method receives unevaluated arguments to the corresponding AST node and should return the evaluated expression.
    """
    def __init__(self):
        self._namespace = namespace()

    def __call__(self, ast):
        op, *args = ast
        if not hasattr(self, op):
            raise RuntimeError(f'unrecognized ast type {op}: {ast!r}')
        return getattr(self, op)(*args)

    def Var(self, name):
        return self._namespace[name]

    def Scope(self, *exprs):
        v = None
        with self._namespace:
            for expr in exprs:
                v = self(expr)
        return v
    def Print(self, *exprs):
        print(*map(self, exprs))

import standard
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
        self._model = standard.Model()
        self._total_order:dict[tuple,tuple|None] = {s:None for s in self.total_order}

    @abstractmethod
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
            raise RuntimeError(f'unrecognized ast type {op}: {ast!r}')
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


class namespace:
    def __init__(self, nro:list[dict]|None=None):
        self.__nro = nro or [{}]

    def __getitem__(self, key):
        return self.__get(key, slice(None))

    @property
    def global_(self):
        return self.__nro[0]

    def __get(self, key, sl:slice):
        for ns in reversed(self.__nro[sl]):
            if key in ns:
                return ns[key]
        raise NameError(key)

    def __setitem__(self, key, value):
        self.__nro[-1][key] = value

    def __enter__(self):
        self.__nro.append({})
        return self

    def __exit__(self, *_):
        return self.__nro.pop()

if __name__ == "__main__":
    e = Evaluator()
    e.eval("""
        %Entrypoint <- Spacing %(Definition / clear)+ EOF
    """)
    e.eval('clear')


