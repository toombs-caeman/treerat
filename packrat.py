from functools import cache
from base2 import ParseError, match
from grammar import *

class Packrat:
    def __init__(self, g:Grammar|str|None = None, startRule:str = 'grammar'):
        match g:
            case str():
                self._grammar = Grammar.from_ast(Packrat().parse(g).ast(g))
            case None:
                self._grammar = Grammar.meta()
            case dict():
                self._grammar = Grammar(g) # copy
            case _:
                raise ValueError(g)

        #self._grammar.eliminate_left_recursion()
        self._grammar.validate()
        self._startRule = startRule

    def parse(self, text:str) -> match:
        # TODO attempt partial cache eviction
        # store old attempts in radix tree
        self._match.cache_clear()
        m = self._match(self._grammar[self._startRule], text, 0)
        if m is None:
            # TODO inspect cache to find the longest match
            # use that to enrich the error here
            raise ParseError(
                ('packrat failed','__stdin__', 0, 0, text),
            )
        return m

    @cache
    def _match(self, c:clause, src:str, idx:int) -> match|None:
        match c:
            # terminals
            case dot():
                if idx < len(src):
                    return match(idx, idx+1)
            case lit():
                if src.startswith(c.inner, idx):
                    return match(idx, idx+len(c.inner))
            case char():
                if idx < len(src) and c.invert ^ any(x[0] <= src[idx] <= x[-1] for x in c.spec):
                    return match(idx, idx+1)
            case ref():
                return self._match(self._grammar[c.name], src, idx)
            # non-terminals
            case label():
                m = self._match(c.inner, src, idx)
                if m is not None:
                    return m._replace(label=c.name)
            case seq():
                stop = idx
                content = []
                for x in c:
                    if (m:=self._match(x, src, stop)) is None:
                        return None
                    content.append(m)
                    stop = m.stop
                return match(idx, stop, content=tuple(content))
            case first():
                for x in c:
                    if (m:=self._match(x, src, idx)):
                        return m
            case yes():
                if (m:=self._match(c.inner, src, idx)):
                    return match(idx, idx)
            case no():
                if (m:=self._match(c.inner, src, idx)) is None:
                    return match(idx, idx)
            case opt():
                if (m:=self._match(c.inner, src, idx)):
                    return m
                return match(idx, idx)
            case zed() | one():
                stop = idx
                content = []
                while (m:=self._match(c.inner, src, stop)):
                    content.append(m)
                    if stop == m.stop:
                        break
                    stop = m.stop
                if content or isinstance(c, zed):
                    return match(idx, stop, content=tuple(content))


def test_meta():
    """this is proof of the fixed point grammar."""
    defined = Grammar.meta()
    src = defined.peg
    calc = Grammar.from_ast(Packrat(defined, 'grammar').parse(src).toAst(src))
    for k in calc:
        rulePEG = f"{k} <- {defined[k].peg}"
        assert defined[k] == calc[k], rulePEG
    assert defined == calc

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
