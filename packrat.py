from functools import cache
from base import ParseError, Parser, match
from grammar import Grammar, T

class Packrat:
    def __init__(self, g:Grammar|str|None = None, startRule:str = 'grammar'):
        match g:
            case str():
                g = Grammar.from_ast(Packrat().parse(g).ast(g))
            case None:
                g = Grammar.meta()
            case Grammar():
                pass
            case _:
                raise ValueError(g)

        g.reduce(startRule)
        g.remove_lr(startRule)
        g.validate()
        self.terms = {id(t):t for t in g.terms(startRule)}
        self.startRule = id(g[startRule])
        self._kinds:set[str] = set(
        t[1] for t in self.terms.values() if t[0] == T.label

        )

    @property
    def kinds(self) -> set[str]:
        return self._kinds

    def ast(self, text:str):
        return self.parse(text).ast(text)

    def parse(self, text:str) -> match:
        # TODO attempt partial cache eviction
        # store old attempts in radix tree
        self._match.cache_clear()
        m = self._match(self.startRule, text, 0)
        if m is None:
            # TODO inspect cache to find the longest match
            # use that to enrich the error here
            raise ParseError(
                ('packrat failed','__stdin__', 0, 0, text),
            )
        return m

    @cache
    def _match(self, c, src:str, idx:int) -> match|None:
        c = self.terms[c]
        match c:
            # terminals
            case [T.dot]:
                if idx < len(src):
                    return match(idx, idx+1)
            case [T.lit, v]:
                assert isinstance(v, str)
                if src.startswith(v, idx):
                    return match(idx, idx+len(v))
            case [T.char| T.ichar, *spec]:
                if idx < len(src) and (c[0] == T.ichar) ^ any(x[0] <= src[idx] <= x[-1] for x in spec):
                    return match(idx, idx+1)
            # non-terminals
            case [T.label, lname, term]:
                m = self._match(id(term), src, idx)
                if m is not None:
                    return m._replace(label=lname)
            case [T.seq, left, right]:
                if (l:=self._match(id(left), src, idx)) is None:
                    return None
                if (r:=self._match(id(right), src, l.stop)) is None:
                    return None
                return match(idx, r.stop, content=(l, r))
            case [T.first, *c]:
                for x in c:
                    if (m:=self._match(id(x), src, idx)):
                        return m
            case [T.no, term]:
                if (m:=self._match(id(term), src, idx)) is None:
                    return match(idx, idx)
            case _:
                raise ValueError(c)


def test_meta():
    """this is proof of the fixed point grammar."""
    defined = Grammar.meta()
    src = defined.peg()
    assert defined.peg(), 'sanity check, this should be the meta grammar'
    calc = Grammar.from_ast(Packrat().ast(src))
    print(calc.peg())
    assert defined.peg() == calc.peg()
    

def test_proto():
    p: Parser = Packrat()
    #assert isinstance(Packrat(), Parser)

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
