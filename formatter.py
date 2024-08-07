class Formatter:
    """
    Reconstruct source from a given ast and parser.

    The output string is not guaranteed to be identical to the original source.
    The only guarantee is that the output string generates ast equal to the input
    (node.start<D-d> and .stop may be different, since those don't affect equality).
    """
    def __init__(self, __from=None, /, **labels:node):
        self.labels = normalize(__from, **labels)
        self.parser = PackratParser(self.labels)

    @cache
    def __call__(self, ast:node) -> str|None:
        pattern = self.labels.get(ast.kind)
        if pattern is None:
            raise FormatError(f'kind in input has no matching pattern: {ast.kind!r}')
            return None # non-strict

        # dispatch call to match ast to pattern
        out:str|None = getattr(self, pattern.kind)(pattern, ast)
        if out is None:
            return None
        # final check that the generated ast matches the input
        if (new_ast:=self.parser(out, start=ast.kind)) != ast:
            raise FormatError(f'ast generated by {pattern.kind} does not correctly parse.', out, ast, new_ast, pattern)
            return None # non-strict
        return out

    def Dot(self, pattern, ast):

        if idx < len(self.__text):
            return node(T.string, self.__text[idx], start=idx, stop=idx+1)

    def String(self, idx, literal):
        if self.__text.startswith(literal, idx):
            return node(T.string, literal, start=idx, stop=idx+len(literal))

    def CharClass(self, idx, *chars):
        if idx >= len(self.__text):
            return
        for crange in chars:
            if crange[0] <= self.__text[idx] <= crange[-1]:
                return node(T.string, self.__text[idx], start=idx, stop=idx+1)

    def Choice(self, idx, *exprs) -> node|None:
        for expr in exprs:
            if (x:=expr(idx)) is not None:
                return x

    def Sequence(self, idx, *exprs):
        c = []
        for expr in exprs:
            if (x:= expr(idx)) is None:
                return None
            idx = x.stop
            c.append(x)
        return node(T.sequence, *c, start=c[0].start, stop=c[-1].stop)

    def OneOrMore(self, idx, expr):
        c = [expr(idx)]
        if c[0] is None:
            return
        while (x:=expr(c[-1].stop)) is not None:
            c.append(x)
        return node(T.sequence, *c, start=c[0].start, stop=c[-1].stop)

    def ZeroOrMore(self, idx, expr):
        c = []
        while (x:=expr(idx)) is not None:
            c.append(x)
            idx = x.stop
        if c:
            return node(T.sequence, *c, start=c[0].start, stop=c[-1].stop)
        return node(T.sequence, start=idx, stop=idx)

    def ZeroOrOne(self, idx, expr):
        if (x:=expr(idx)) is None:
            return node(T.sequence, start=idx, stop=idx)
        return x

    def Lookahead(self, idx, expr):
        if expr(idx) is not None:
            return node(T.sequence, start=idx, stop=idx)

    def NotLookahead(self, idx, expr):
        if expr(idx) is None:
            return node(T.sequence, start=idx, stop=idx)

    def Node(self, idx, name, expr):
        if (x:=expr(idx)):
            return node(T.node, name, x, start=x.start, stop=x.stop)

    def Argument(self, idx, expr):
        if (x:=expr(idx)):
            return node(T.argument, x, start=x.start, stop=x.stop)

    def Label(self, idx, name):
        if (x:=self.funcs[name](idx)):
            return node(T.label, name, x, start=x.start, stop=x.stop)

    def Index(self, idx, name, offset):
        # this should be resolved into calls to self.Label during initialization
        raise NotImplementedError
