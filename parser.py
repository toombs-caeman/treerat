import enum
from functools import cache

#__all__ = ['BuildParser', 'T']

"""
'specs' are a function serialized into a lisp-like syntax
each function is a list with the first element being T that indicates the function, and following by string and spec arguments to that function

This allows a spec to be valid json.
"""
# the types recognized in spec
T = enum.Enum('T', (
    'Dot',
    'String',  # a sequence of one or more characters
    #'CharacterClass', # a choice between one or more strings

    'Choice',
    'Sequence',

    'ZeroOrOne',
    'ZeroOrMore',
    'OneOrMore',

    #'Lookahead',
    'NotLookahead',

    'Argument',
    'Index',
    'Node',
    'Label',
))

class Parser:
    def __init__(self, spec):
        """Initialize the parser according the parsing spec"""
        raise NotImplementedError
    def __call__(self, text:str):
        """parse text into a parse tree"""
        raise NotImplementedError
    def fmt(self, tree) -> str:
        """
        Produces a string that would parse to the given tree with this parser.

        This is not necessarily the exact string that was used to generate the tree.
        """
        
        raise NotImplementedError

def BuildParser(spec, **labels) -> Parser:
    # depending on the spec, more efficent parsers could potentially be generated
    # but for now, always return a packrat
    return PackratParser(spec, **labels)


class PackratParser(Parser):
    def __init__(self, spec, **labels):
        self.spec = spec
        self.labels = labels
        # curry all functions, add in the cache, then append to funcs
        self.funcs = []
        self.label_funcs = {}
        def walk(spec):
            if isinstance(spec, str):
                return walk((T.String, spec))
            t, *args = spec
            if t == T.Label:
                name = args[0]
                return lambda idx:self.label_funcs[name](idx)
            if t == T.Index:
                name, offset = args
                if (name, offset) not in self.label_funcs:
                    l, *a = labels[name]
                    self.label_funcs[name, offset] = walk((l, a[offset:]))
                return lambda idx:self.label_funcs[name, offset](idx)

            if t == T.Node:
                name, expr = args
                args = name, walk(expr)
            elif t != T.String:
                args = tuple(walk(s) for s in args)
            # TODO disable caching for Index and Label, since they are just pass-through
            f = cache(lambda idx:getattr(self, t.name)(idx,*args))
            self.funcs.append(f)
            return f
        for label, s in labels.items():
            self.label_funcs[label] = walk(s)
        # the toplevel spec forms the entrypoint
        self.entrypoint = walk(spec)

        # TODO setup inverse parsing (fmt)
        # create a lens that lets you iterate over a trees arguments
        # paths : List[List[int]] with negative numbers indicating going up the tree


    def __call__(self, text):
        self.text = text
        for f in self.funcs:
            f.cache_clear()
        result = self.entrypoint(0)
        if result:
            return self._trim(result[1])
        return None

    def fmt(self, tree) -> str:
        # raise ValueError if the tree cannot match the spec
        def walk(spec, tree):
            match tree:
                case [T.Node, name, body]:
                    pass
                case [T.Argument, body]:
                    pass
                case list():
                    pass
                case str():
                    pass
                case x:
                    raise ValueError(f'unexpected value in tree: {x!r}')
            yield ''
        return ''.join(walk(self.spec, tree))
        

    def _trim(self, obj, ancestor=None, memo=None):
        # reduce nesting to just Nodes
        # under the top level, return everything
        # need to filter out arguments, nodes
        # join sequential strings and flatten nested lists
        match obj:
            case [T.Node, name, body]:
                memo = [name]
                self._trim(body, T.Node, memo)
                return memo
            case [T.Argument, body]:
                body = self._trim(body, T.Argument, memo)
                if memo:
                    memo.append(body)
                return body
            case list():
                out = []
                for a in obj:
                    x = self._trim(a, ancestor, memo)
                    if isinstance(x, str) and out and isinstance(out[-1], str):
                        out[-1]+=x
                    else:
                        out.append(x)
                if len(out) == 1:
                    return out[0]
                return out
            case _:
                return obj

    # lexing functions return a tuple (idx, content) if it matches else None
    # idx is the index from which to continue
    # content may be
    #   None: filtered out
    #   str: literal text
    #   list:, or a Node

    def Dot(self, idx):
        if len(self.text) > idx:
            return idx + 1, self.text[idx]

    def String(self, idx, literal):
        if self.text.startswith(literal, idx):
            return idx + len(literal), literal

    def Choice(self, idx, *args):
        # return the first result that's not None
        return next((x for p in args if (x:=p(idx))), None)

    def Sequence(self, idx, *exprs):
        c = []
        for expr in exprs:
            if ( x:= expr(idx)) is None:
                return None
            l, v = x
            idx = l
            c.append(v)
        return idx, c

    def OneOrMore(self, idx, expr):
        c = []
        if (x:=expr(idx)) is None:
            return
        l, v = x
        idx = l
        c.append(v)
        while (x:=expr(idx)) is not None:
            l, v = x
            idx = l
            c.append(v)
        return idx, c

    def ZeroOrMore(self, idx, expr):
        c = []
        while (x:=expr(idx)) is not None:
            l, v = x
            idx = l
            c.append(v)
        return idx, c

    def ZeroOrOne(self, idx, expr):
        if (x:=expr(idx)) is None:
            return idx, None
        return x

    def NotLookahead(self, idx, expr):
        if expr(idx) is None:
            return idx, None

    def Node(self, idx, name, expr):
        if (x:=expr(idx)) is None:
            return None
        l, v = x
        return l, [T.Node, name, v]

    def Argument(self, idx, expr):
        if (x:=expr(idx)) is None:
            return
        l, v = x
        return l, [T.Argument, v]

    def Label(self):
        """This is never actually called, as labels are handled in __init__"""
        raise NotImplementedError

    def Index(self):
        """This is never actually called, as label indexes are handled in __init__"""
        raise NotImplementedError


