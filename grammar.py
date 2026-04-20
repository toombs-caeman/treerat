from collections import namedtuple
from typing import Iterable, NamedTuple, Self
from base2 import ast

"""
a description parsing expression grammars for parsing generators

TODO docstrings with definitions, motivation

https://en.wikipedia.org/wiki/Parsing_expression_grammar
"""

# TODO serializers? as a way to load/restore grammars
# struct + base64?
# json with custom encoder?
# https://docs.python.org/3/library/base64.html
# https://docs.python.org/3/library/struct.html
# https://docs.python.org/3/library/json.html

type clause = terminal | nonterminal
type terminal = dot | lit | char | ref
type nonterminal = label | seq | first | yes | no | opt | zed | one

def unescape(s:str) -> str:
    """convert escaped strings to their non-escaped form."""
    # TODO handle octal values
    for old, new in (
        (r'\n', '\n'),
        (r'\r', '\r'),
        (r'\t', '\t'),
        (r'\[', '['),
        (r'\]', ']'),
        (r'\"', '"'),
        (r"\'", "'"),
        (r'\\','\\'),
    ):
        s = s.replace(old, new)
    return s

class Grammar(dict):
    @classmethod
    def meta(cls) -> 'Grammar':
        # TODO align labels here with names of namedtuple types
        G = cls()
        G['grammar'] = seq(ref('sp'), zed(ref('definition')), no(dot()))
        G['definition'] = label('definition',seq(ref('identifier'), lit('<-'), ref('sp'), ref('E')))
        G['EOL'] = first(lit('\r\n'), lit('\n'), lit('\r'))
        G['comment'] = seq(lit('#'), zed(seq(no(ref('EOL')), dot())), ref('EOL'))
        G['sp'] = zed(first(lit(' '), lit('\t'), ref('EOL'), ref('comment')))
        G['char'] = first(
            seq(lit('\\'), char(*"nrt'\"[]\\")),
            seq(lit('\\'), char('02'), char('07'), char('07')),
            seq(lit('\\'), char('07'), opt(char('07'))),
            seq(no(lit('\\')), dot()),
        )
        G['class'] =  seq(
            label('char', seq(
                lit('['), zed(seq(
                    no(lit(']')),
                    # TODO don't love this
                    label('crange', first(
                        seq(ref('char'), lit('-'), ref('char')),
                        ref('char')
                    )),
                )),
                lit(']'),
            )),
            ref('sp')
        )
        G['identifier'] = seq(label(
            'identifier',
            seq(char('az', 'AZ', '_'), zed(char('az', 'AZ', '_', '09'))),
        ), ref('sp'))
        q = lit("'")
        qq = lit('"')
        G['lit'] = seq( first(
            seq(q, label('lit',zed(seq(no(q), ref('char')))), q),
            seq(qq, label('lit',zed(seq(no(qq), ref('char')))), qq),
        ), ref('sp'))
        G['E'] = first( # choice/first
            label('first',seq(ref('E'), lit('/'), ref('sp'), ref('E1'))),
            ref('E1')
        )
        G['E1'] = first( # sequence
            label('seq', seq(ref('E1'), ref('E2'))),
            ref('E2')
        )
        G['E2'] = first( # prefix
            label('yes', seq(lit('&'), ref('sp'), ref('E3'))),
            label('no',seq(lit('!'), ref('sp'), ref('E3'))),
            label('label',seq(ref('identifier'), lit(':'), ref('sp'), ref('E2'))),
            ref('E3')
        )
        G['E3'] = first( # postfix
            label('opt', seq(ref('E4'), lit('?'), ref('sp'))),
            label('zed', seq(ref('E4'), lit('*'), ref('sp'))),
            label('one', seq(ref('E4'), lit('+'), ref('sp'))),
            ref('E4')
        )
        G['E4'] = first( # terminal and paren
            label('ref',seq(ref('identifier'), no(lit('<-')))),
            ref('lit'),
            ref('class'),
            label('dot', seq(lit('.'), ref('sp'))),
            seq(lit('('), ref('sp'), ref('E'), lit(')'), ref('sp')),
        )
        G.validate()
        return G

    @classmethod
    def from_ast(cls, a:Iterable[ast]) -> 'Grammar':
        g = Grammar()
        kernel = {f.__name__:f for f in [ref, label, char, seq, first, no, zed, one, opt, yes]}
        kernel['definition'] = g.__setitem__
        kernel['identifier'] = lambda x:x
        kernel['dot'] = lambda _:dot()
        kernel['lit'] = lambda s:lit(unescape(s))
        kernel['crange'] = lambda s:unescape(s)[::2]
        def eval(a:ast|str):
            if isinstance(a, str):
                return a
            return kernel[a[0]](*map(eval, a[1:]))
        # run kernel
        for rule in a:
            eval(rule)
        return g

    def eliminate_left_recursion(self):
        # https://www.geeksforgeeks.org/dsa/removing-direct-and-indirect-left-recursion-in-a-grammar/
        # TODO identify sources of indirect left recursion
        # TODO convert all indirect left recursion into direct left recursion
        # TODO eliminate direct left recursion
        raise NotImplementedError()

    def validate(self):
        # TODO detect ref to undefined rule
        # detect `a <- a`, which is ill-defined.
        for k,v in self.items():
            if isinstance(v, ref) and v.name == k:
                raise ValueError(f"rule {k} is ill-defined (rule in form `a <- a`).")
    @property
    def peg(self) -> str:
        return '\n'.join(
            f"{k} <- {v.peg}"
            for k, v in self.items()
        )

# TERMINALS
class dot(NamedTuple):
    @property
    def peg(self) -> str:
        return '.'

class lit(NamedTuple):
    """match a """
    inner: str
    @property
    def peg(self) -> str:
        return repr(self.inner)
    @classmethod

    def escape(cls, s:str) -> str:
        # TODO this isn't perfect
        # doesn't handle octal values for example
        t = {
            '\n':r'\n',
            '\t':r'\t',
            '\r':r'\r',
            '\\':r'\\',
        }
        return ''.join(t.get(c, c) for c in s)

#TODO NamedTuple doesn't play nice with overriding __new__
#this is functionally equivalent, but doesn't play nice with type hints
class char(namedtuple('char', ['invert', 'spec'])):
    """match a single character from a set (or inverted set)."""
    def __new__(cls, *spec:str, invert:bool=False) -> Self:
        assert all(len(s) <= 2 for s in spec)
        return super().__new__(cls, invert, spec)

    @property
    def peg(self) -> str:
        c = ['^' if self.invert else '']
        for rule in self.spec:
            if len(rule) == 1:
                c.append(rule)
            else:
                c.extend((rule[0], '-', rule[-1]))
        return f"[{''.join(map(char.escape, c))}]"

    @classmethod
    def escape(cls, c:str) -> str:
        c = lit.escape(c)
        return {'[':'\\[', ']':'\\]'}.get(c, c)

class ref(NamedTuple):
    """refer to a clause by name."""
    name: str
    @property
    def peg(self) -> str:
        return self.name

# NONTERMINALS

class label(NamedTuple):
    """label a clause."""
    name: str
    inner:clause
    @property
    def peg(self) -> str:
        return f"{self.name}:{self.inner.peg}"

class seq(tuple):
    """match inner clauses sequentially."""
    def __new__(cls, *inner:clause) -> clause:
        match len(inner):
            case 0:
                raise ValueError()
            case 1:
                return inner[0]
            case _:
                # `(a b) c` -> `a b c`
                c = []
                for x in inner:
                    if isinstance(x, seq):
                        c.extend(x)
                    else:
                        c.append(x)
                return super().__new__(cls, c)
    def __str__(self) -> str:
        return f"{type(self).__name__}{super().__str__()}"
    @property
    def peg(self) -> str:
        return f"({' '.join(x.peg for x in self)})"


class first(tuple):
    """match on the first matching inner clause."""
    def __new__(cls, *inner:clause) -> clause:
        match len(inner):
            case 0:
                raise ValueError()
            case 1:
                return inner[0]
            case _:
                # `(a / b) / c` == `a / b / c`
                c = []
                for x in inner:
                    if isinstance(x, first):
                        c.extend(x)
                    else:
                        c.append(x)
                return super().__new__(cls, c)

    def __str__(self) -> str:
        return f"{type(self).__name__}{super().__str__()}"
    @property
    def peg(self) -> str:
        return f"({' / '.join(x.peg for x in self)})"

class no(NamedTuple):
    """match if the inner clause doesn't."""
    inner: clause
    @property
    def peg(self) -> str:
        return f"!{self.inner.peg}"

class yes(NamedTuple):
    """match the inner clause without consuming input."""
    inner: clause
    @property
    def peg(self) -> str:
        return f"&{self.inner.peg}"

class zed(NamedTuple):
    """match a clause zero or more times."""
    inner: clause
    @property
    def peg(self) -> str:
        return f"{self.inner.peg}*"

class one(NamedTuple):
    """match a clause one or more times."""
    inner: clause
    @property
    def peg(self) -> str:
        return f"{self.inner.peg}+"

class opt(NamedTuple):
    """match a clause zero or one times."""
    inner: clause
    @property
    def peg(self) -> str:
        return f"{self.inner.peg}?"

if __name__ == "__main__":
    print(Grammar.meta().peg)
    
