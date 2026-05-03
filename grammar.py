"""
represent PEG in a normalized form, graph reduction engine?
"""
from collections import defaultdict
from functools import cache, cached_property
from enum import IntEnum, auto
import re
from typing import Iterable

from base2 import ast


class T(IntEnum):
    # this also encodes operator precedence (for Grammar.peg())
    # terminal
    dot = auto()  # .
    char = auto()  # []
    ichar = auto()  # [^]
    lit = auto()  # ""
    re = auto()  # `` regex
    # nonterminal
    label = auto()  # label:
    no = auto()  # !
    yes = auto()  # &
    one = auto()  # +
    zed = auto()  # *
    opt = auto()  # ?
    seq = auto()  # ' '
    first = auto()  # /
    # Grammar uses recursive data structures internally instead of ref,
    # but in situations where that can't be done:
    # ref is a reference to a named rule in the grammar.
    ref = auto()

# TODO expand character ranges, deduplicate
# return [T.char, ''.join({chr(x) for s in spec for x in range(ord(s[0]), ord(s[-1])-1)})]


def unescape(s: str) -> str:
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
        (r'\\', '\\'),
    ):
        s = s.replace(old, new)
    return s


def dot():
    return [T.dot]


def char(*spec):
    assert all(0 < len(s) <= 2 for s in spec)
    return [T.char, *spec]


def ichar(*spec):
    assert all(0 < len(s) <= 2 for s in spec)
    return [T.ichar, *spec]


def lit(s):
    return [T.lit, s]


def label(name, term):
    return [T.label, name, term]


def seq(term, *rest) -> list:
    match len(rest):
        case 0:
            return term
        case 1:
            return [T.seq, term, rest[0]]
        case _:
            return [T.seq, term, seq(*rest)]


def first(term, *rest) -> list:
    match len(rest):
        case 0:
            return term
        case 1:
            return [T.first, term, rest[0]]
        case _:
            return [T.first, term, first(*rest)]


def no(term):
    return [T.no, term]


def yes(term):
    return [T.yes, term]


def one(term):
    return [T.one, term]


def zed(term):
    return [T.zed, term]


def opt(term):
    return [T.opt, term]


def regex(pattern):
    return [T.re, pattern]


def ref(name):
    return [T.ref, name]


type term = list[T | term | str]


class Grammar(dict):
    def __getitem__(self, key: str, /) -> list:
        # act like defaultdict(list)
        return self.setdefault(key, [])

    def __setitem__(self, key: str, value: list):
        if key not in self:
            return super().__setitem__(key, value)
        # preserve the id of the current value
        # but swap its contents
        self[key][:] = value
        self.cache_clear()

    def cache_clear(self):
        # TODO clear all the caches
        for cache in ['validate', 'terms', 'peg', 'deduplicate']:
            getattr(self, cache).cache_clear()
        for cached_property in ['parents']:
            if cached_property in self.__dict__:
                delattr(self, cached_property)

    @cache
    def validate(self):
        # TODO more validation

        # make sure all rules have a definition (not empty)
        # and that no rule is `a <- a`
        return all(x and (x != x[0]) for x in self.values())

    def copy(self):
        raise NotImplementedError('this is tricky')

    def __hash__(self):
        # give us a fake hash, otherwise we can't use cache because of self
        # TODO what sins have I committed with this?
        return hash(id(self))

    @cache
    def terms(self, key: str | None = None) -> tuple[term, ...]:
        """produce a post order deduplicated topological sort of terms reachable from a given rule"""
        # useful for generating a pika parser
        memo = set()

        def dfs(n):
            if id(n) in memo:
                return
            memo.add(id(n))
            match n:
                case [T.dot | T.lit | T.char | T.ichar, *_]:
                    pass
                case [T.seq | T.first, left, right]:
                    yield from dfs(left)
                    yield from dfs(right)
                case [T.label, _, term] | [T(), term]:
                    yield from dfs(term)
            yield n
        values = self.values() if key is None else (self[key],)
        out = []
        for v in values:
            out.extend(dfs(v))
        return tuple(out)

    def remove_lr(self, key=None):
        """eliminate left recursion"""
        if key is None:
            for k in list(self):
                self.remove_lr(k)
            return
        memo = set()

        def dfs(n):
            if id(n) in memo:
                if n == self[key]:
                    # print(key, n[0].name, self.pe(n, shortcircuit=False))
                    return n
                return
            memo.add(id(n))
            match n:
                case [T.dot | T.lit | T.char | T.ichar, *_]:
                    return
                case [T.first, left, right]:
                    return dfs(left) or dfs(right)
                case [T.seq, left, right]:
                    if (ret := dfs(left)):
                        return ret
                    if self.nullable(left):
                        return dfs(right)
                case [T.label, _, term] | [T(), term]:
                    return dfs(term)
                case _:
                    raise ValueError(n)

        while True:
            memo.clear()
            problem = dfs(self[key])
            if not problem:
                break
            match problem:
                case [T.first, [T.seq, lilprob, x], right] if lilprob == problem:
                    ppeg = self.pe(problem, min(T), shortcircuit=False)
                    self._replace(problem, x)
                    name = self._getname('LR')
                    self[name] = first(seq(x, self[name]), self._)
                    solution = seq(right, self[name])
                    problem[:] = solution

                case _:
                    mea_culpa = f"don't know how to resolve {
                        self.pe(problem, min(T), shortcircuit=False)}"
                    raise NotImplementedError(mea_culpa)

    def nullable(self, term) -> bool:
        memo = {}

        def dfs(n):
            if id(n) in memo:
                return memo[id(n)]
            ret = None
            memo[id(n)] = ret
            match n:
                case [T.dot | T.lit | T.char | T.ichar, *_]:
                    ret = False
                case [T.first, left, right]:
                    ret = dfs(left) or dfs(right)
                case [T.seq, left, right]:
                    ret = dfs(left) and dfs(right)
                case [T.no | T.yes | T.opt | T.zed, term]:
                    return True
                case [T.label, _, term] | [T(), term]:
                    return dfs(term)
                case _:
                    raise ValueError(f"dunno boss {self.pe(n)}")
            memo[id(n)] = ret
            return ret
        return dfs(term)

    @cached_property
    def parents(self) -> dict[int, list[term]]:
        """get the parents of terms by id"""
        # have to do it this way because terms are not hashable
        out = defaultdict(list)
        for n in self.terms():
            match n:
                case [T.dot | T.lit | T.char | T.ichar, *_]:
                    pass
                case [T.seq | T.first, left, right]:
                    out[id(left)].append(n)
                    out[id(right)].append(n)
                case [T.label, _, term] | [T(), term]:
                    out[id(term)].append(n)
        return out

    @cache
    def deduplicate(self):
        """deduplicate equivalent subclauses"""
        for i, oldTerm in enumerate(self.terms()):
            for newTerm in self.terms()[:i]:
                if oldTerm == newTerm and oldTerm is not newTerm:
                    # self._replace can be much simpler if we don't use it here
                    # self._replace(oldTerm, newTerm)
                    for p in self.parents[id(oldTerm)]:
                        match p:
                            case [T.dot | T.lit | T.char | T.ichar, *_]:
                                raise ValueError(
                                    'terminal is supposedly a parent')
                            case [T.seq | T.first, left, right]:
                                if left == oldTerm:
                                    p[1] = newTerm
                                if right == oldTerm:
                                    p[2] = newTerm
                            case [T.label, *_]:
                                p[2] = newTerm
                            case [T(), _]:
                                p[1] = newTerm
                    self.cache_clear()

    def _getname(self, like: str = '') -> str:
        """get a rule name that hasn't been used yet."""
        base = like.rstrip('0123456789')
        if base not in self:
            return base
        count = 1
        while (key := f"{base}{count}") in self:
            count += 1
        return key

    def _replace(self, oldTerm, newTerm):
        # TODO most of the time this simple way works fine
        # but it doesn't work for deduplication.
        oldTerm[:] = newTerm
        self.cache_clear()

    def trim(self, key: str):
        """remove rules which are not reachable from the given rule name"""
        evilTwin = {id(v): k for k, v in self.items()}
        for t in self.terms(key):
            if id(t) in evilTwin:
                del evilTwin[id(t)]
        for k in evilTwin.values():
            del self[k]

    _ = lit('')

    def enable_regex(self, key=None):
        """graph rewrite operations"""
        def fmt(t):
            if t[0] == T.lit:
                return re.escape(t[1])
            return self.pe(t)

        for t in self.terms(key):
            match t:
                case [T.seq, [T.lit | T.char | T.ichar, *_], [T.lit | T.char | T.ichar, *_]]:
                    self._replace(t, regex(f"{fmt(t[1])}{fmt(t[2])}"))
                case [T.seq, [T.re, pattern], [T.lit | T.char | T.ichar, *_]]:
                    self._replace(t, regex(f"(?:{pattern}){fmt(t[2])}"))
                case [T.seq, [T.lit | T.char | T.ichar, *_], [T.re, pattern]]:
                    self._replace(t, regex(f"{fmt(t[2])}(?:{pattern})"))
                case [T.first, [T.lit | T.char | T.ichar, *_], [T.lit | T.char | T.ichar, *_]]:
                    self._replace(t, regex(f"{fmt(t[1])}|{fmt(t[2])}"))
                case [T.first, [T.re, pattern], [T.lit | T.char | T.ichar, *_]]:
                    self._replace(t, regex(f"(?:{pattern})|{fmt(t[2])}"))
                case [T.first, [T.lit | T.char | T.ichar, *_], [T.re, pattern]]:
                    self._replace(t, regex(f"{fmt(t[2])}|(?:{pattern})"))

    def reduce(self, key=None):
        """graph rewrite operations"""
        # TODO this also eliminates * ? + at the cost of more rules
        # TODO not entirely sure if this always does all reductions,
        # but it probably will because of how terms() is sorted
        for t in self.terms(key):
            match t:
                case [T.seq, self._, a] | [T.seq, a, self._]:
                    # ε a -> a
                    # a ε -> a
                    self._replace(t, a)
                case [T.first, self._, _]:
                    # ε / a -> ε
                    self._replace(t, self._)
                case [T.yes, a]:
                    # &a -> !!a
                    self._replace(t, no(no(a)))
                case [T.opt, a]:
                    # a? -> a / ε
                    self._replace(t, first(a, self._))
                case [T.one, a]:
                    # a+ -> a a*
                    self._replace(t, seq(a, zed(a)))
                case [T.seq, [T.lit, a], [T.lit, b]]:
                    # 'a' 'b' -> 'ab'
                    self._replace(t, lit(f"{a}{b}"))
                case [T.first, [T.lit, a], [T.lit, b]] if len(a) == len(b) == 1:
                    # 'a' / 'b' -> [ab]
                    self._replace(t, char(a, b))
                case [T.first, [T.char, *spec], [T.lit, b]] | \
                     [T.first, [T.lit, b], [T.char, *spec]] if len(b) == 1:
                    # [a] / 'b' -> [ab]
                    #  'b' / [a] -> [ab]
                    self._replace(t, char(*spec, b))
                case [T.zed, a]:
                    name = self._getname('REP')
                    self[name] = first(seq(a, self[name]), self._)
                    self._replace(t, self[name])
                # TODO normalize char spec
                # TODO (a b) c -> a (b c)
                # TODO (a / b) / c -> a / (b / c)

        if key is not None:
            self.trim(key)
        self.deduplicate()

    @property
    def size(self):
        return len(self.terms())

    def __str__(self) -> str:
        return self.peg()

    @cache
    def peg(self, key=None):
        if key is None:
            return '\n'.join(self.peg(k) for k in sorted(self))
        return f"{key} <- {self.pe(super().__getitem__(key), max(T), False)}"

    def pe(self, expr, outerT: T = max(T), shortcircuit=True):
        """format a parsing expression"""
        # TODO this may no longer be possible after eliminating left recursion
        if shortcircuit:
            for k, v in self.items():
                if expr == v:
                    return k
        match expr:
            case [T.dot]:
                out = '.'
            case [T.char, *spec] | [T.ichar, *spec]:
                # TODO do better
                def escape(x):
                    if x == ']':
                        return r'\]'
                    return repr(x)[1:-1]
                inv = '^' if expr[0] == T.ichar else ''
                spec = ''.join(
                    f"{escape(x[0])}-{escape(x[-1])}"
                    if len(x) > 1 else escape(x)
                    for x in expr[1:]
                )
                out = f"[{inv}{spec}]"
            case [T.lit, value]:
                out = repr(value)
            case [T.re, pattern]:
                return f"`{repr(pattern)[1:-1]}`"
            case [T.label, name, term]:
                out = f"{name}:{self.pe(term, T.label)}"
            case [T.seq, left, right]:
                out = f"{self.pe(left, T.seq)} {self.pe(right, T.seq)}"
            case [T.first, left, right]:
                out = f"{self.pe(left, T.first)} / {self.pe(right, T.first)}"
            case [T.no, term]:
                out = f"!{self.pe(term, T.no)}"
            case [T.yes, term]:
                out = f"&{self.pe(term, T.yes)}"
            case [T.one, term]:
                out = f"{self.pe(term, T.one)}+"
            case [T.zed, term]:
                out = f"{self.pe(term, T.zed)}*"
            case [T.opt, term]:
                out = f"{self.pe(term, T.opt)}?"
            case _:
                raise ValueError(expr)
        if expr[0] > outerT:
            return f"({out})"
        return out

    @classmethod
    def meta(klass):

        G = klass()
        G['grammar'] = seq(G['sp'], zed(G['definition']), no(dot()))
        G['definition'] = label('definition', seq(
            G['identifier'], lit('<-'), G['sp'], G['E']))
        G['EOL'] = first(lit('\r\n'), lit('\n'), lit('\r'))
        G['comment'] = seq(lit('#'), zed(seq(no(G['EOL']), dot())), G['EOL'])
        G['sp'] = zed(first(lit(' '), lit('\t'), G['EOL'], G['comment']))
        G['char'] = first(
            seq(lit('\\'), char(*"nrt'\"[]\\")),
            seq(lit('\\'), char('02'), char('07'), char('07')),
            seq(lit('\\'), char('07'), opt(char('07'))),
            seq(no(lit('\\')), dot()),
        )
        G['class'] = seq(
            label('char', seq(
                lit('['), zed(seq(
                    no(lit(']')),
                    # TODO don't love this
                    label('crange', first(
                        seq(G['char'], lit('-'), G['char']),
                        G['char']
                    )),
                )),
                lit(']'),
            )),
            G['sp']
        )
        G['identifier'] = seq(label(
            'identifier',
            seq(char('az', 'AZ', '_'), zed(char('az', 'AZ', '_', '09'))),
        ), G['sp'])
        q = lit("'")
        qq = lit('"')
        G['lit'] = seq(first(
            seq(q, label('lit', zed(seq(no(q), G['char']))), q),
            seq(qq, label('lit', zed(seq(no(qq), G['char']))), qq),
        ), G['sp'])
        G['E'] = first(  # choice/first
            label('first', seq(G['E1'], lit('/'), G['sp'], G['E'])),
            G['E1']
        )
        G['E1'] = first(  # sequence
            label('seq', seq(G['E2'], G['E1'])),
            G['E2']
        )
        G['E2'] = first(  # prefix
            label('yes', seq(lit('&'), G['sp'], G['E3'])),
            label('no', seq(lit('!'), G['sp'], G['E3'])),
            label('label', seq(G['identifier'], lit(':'), G['sp'], G['E2'])),
            G['E3']
        )
        G['E3'] = first(  # postfix
            label('opt', seq(G['E4'], lit('?'), G['sp'])),
            label('zed', seq(G['E4'], lit('*'), G['sp'])),
            label('one', seq(G['E4'], lit('+'), G['sp'])),
            G['E4']
        )
        G['E4'] = first(  # terminal and paren
            label('ref', seq(G['identifier'], no(lit('<-')))),
            G['lit'],
            G['class'],
            label('dot', seq(lit('.'), G['sp'])),
            seq(lit('('), G['sp'], G['E'], lit(')'), G['sp']),
        )
        return G

    @classmethod
    def from_ast(cls, a: Iterable[ast]) -> 'Grammar':
        g = Grammar()
        kernel = {f.__name__: f for f in [
            label, char, seq, first, no, zed, one, opt, yes]}
        kernel['definition'] = g.__setitem__
        kernel['identifier'] = lambda x: x
        kernel['dot'] = lambda _: dot()
        kernel['lit'] = lambda s: lit(unescape(s))
        kernel['crange'] = lambda s: unescape(s)[::2]
        kernel['ref'] = lambda s: g[s]

        def eval(a: ast | str):
            if isinstance(a, str):
                return a
            return kernel[a[0]](*map(eval, a[1:]))
        # run kernel
        for rule in a:
            eval(rule)
        return g


def test_lr():
    g = Grammar()
    g['a'] = first(seq(g['a'], lit(' bap')), lit('boom'))
    goal = Grammar()
    goal['a'] = seq(lit('boom'), goal['LR'])
    goal['LR'] = first(seq(lit(' bap'), goal['LR']), lit(''))
    assert g != goal
    g.remove_lr()
    assert str(g) == str(goal)
    assert False, 'TODO indirect case'


def test_peg():
    # TODO don't use meta, since it could change
    print(Grammar.meta().peg())
    pass


def test_reduce():
    # TODO
    g = Grammar.meta()
    g.reduce()
    print(g)
    g.enable_regex()
    print()
    print()
    print()
    print(g)


def test_deduplicate():
    g = Grammar.meta()
    oldsize = len(g.terms())
    g.deduplicate()
    assert len(g.terms()) < oldsize


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
    # test_lr()
    # test_peg()
    test_reduce()
