import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache, cached_property
from collections import defaultdict, namedtuple
from typing import Callable, Generator, Hashable, Iterable, Self
from base import Parser, ParseError
import heapq

"""
clauses:
* reference
* terminal
    * string
    * character class
    * dot
* nonterminal
    * core
        * sequence
        * first
        * not
        * zeroplus
    * derived
        * oneplus - seq((), zeroplus(()))
        * optional - first((), '')
        * follows - not(not())

stages:
* rules, defined with weak references
* eliminate references and duplicate clauses
* extract structure
    * start clause (highest index)
    * clause index
    * seed parents
"""
@dataclass
class clause:
    pass

class T:
    # clause types

    a = 'seq' # match a sequence of clauses
    o = 'first' # match the first valid subclause
    e = 'eq' # match a character
    r = 'range' # match a range of characters
    d = 'dot' # match any character
    ae = 'string' # match a string
    oer = 'cclass' # match a character class

    # terminal nodes
    # string

type memo = dict[tuple[int, ParseClause], ParseNode]

@dataclass
class ParseNode:
    # debug
    clause: ParseClause
    # span
    content:tuple[ParseNode, ...]
    start: int
    stop: int
    label: str = ''
    def clean(self) -> ParseNode | None:
        """produce a simplified tree, where every node is labelled."""
        pass
    def cast[T:type](self, node_cast:dict[str, T]) -> T:
        return node_cast[self.label](*(x.cast(node_cast) for x in self.content))
    def __str__(self, src:str|None=None):
        base = f"{self.label}[{self.start}:{self.stop}]"
        if src is None:
            return base
        return f"{base} {src[self.start:self.stop]!r}"
    def format(self,src:str|None=None, max_width:int=80, prefix:str='', next_p=''):
        out = [f"{prefix}{next_p}{self.__str__(src)}"]
        match next_p:
            case '├':
                prefix += '│'
            case '└':
                prefix += ' '
        if self.content:
            for c in self.content[:-1]:
                out.append(c.format(src, max_width, prefix, '├'))
            out.append(self.content[-1].format(src, max_width, prefix, '└'))

        chars = '│├└ '
        return '\n'.join(out)

class grammar:
    def __init__(self, startRule:str):
        self.startRule = startRule
        self.rules: dict[str, ParseClause] = {}
    def __getitem__(self, key:str) -> Reference:
        return Reference(key, self)
    def __setitem__(self, key, value:ParseClause):
        self.rules[key] = value


def traverse(
    start:ParseClause,
    succ:Callable[[NonTerminal], Iterable[ParseClause]]=lambda n:n.spec
):
    # post order depth first search
    seen = set()
    def dfs(n):
        while isinstance(n, Reference):
            n = n.rule
        if n in seen:
            return
        seen.add(n)
        if isinstance(n, NonTerminal):
            for child in succ(n):
                yield from dfs(child)
        yield n
    return dfs(start)

## CLAUSES

class ParseClause(ABC):
    label: str = ''
    spec = None
    # nullable is true if this clause can match the empty string, false if it can't, and none if hasn't been determined yet
    nullable:bool|None = None
    @abstractmethod
    def match(self, srcIdx:int, src: str, memo:memo) -> ParseNode | None:
        """either produce a node or fail to match."""
    @abstractmethod
    def startswith(self, child: ParseClause) -> bool:
        """return True if the child clause could match at the start of this clause"""
    @property
    def _label(self):
        return self.label + ':' if self.label else ''


class Reference(ParseClause):
    def __init__(self, name:str, grammar:grammar):
        self.label = name
        self.grammar = grammar
    @property
    def rule(self) -> ParseClause:
        return self.grammar.rules[self.label]
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        return self.rule.match(srcIdx, src, memo)
    def startswith(self, child: ParseClause) -> bool:
        return self.rule.startswith(child)
    def __str__(self) -> str:
        return self.label

# TERMINALS

class Terminal(ParseClause):
    def startswith(self, child: ParseClause) -> bool:
        return self == child

class String(Terminal):
    def __init__(self, spec:str, *, label='') -> None:
        self.spec = spec
        self.label = label
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        if not src.startswith(self.spec, srcIdx):
            return None
        return ParseNode(clause=self, content=(), start=srcIdx, stop=srcIdx+len(self.spec), label=self.label)
    def __str__(self) -> str:
        return f"{self._label}{self.spec!r}"

class Dot(Terminal):
    def __init__(self, *, label='') -> None:
        self.label = label
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        if srcIdx < len(src):
            return ParseNode(clause=self, content=(), start=srcIdx, stop=srcIdx+1, label=self.label)
        return None
    def __str__(self) -> str:
        return self._label + '.'

class CClass(Terminal):
    def __init__(self, *spec:str, label='') -> None:
        self.inv = spec[0] == '^'
        self.spec = spec[1:] if self.inv else spec
        self.label = label
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        if srcIdx < len(src) and self.inv ^ any(
            r[0] <= src[srcIdx] <= r[-1] for r in self.spec
        ):
            return ParseNode(clause=self, content=(), start=srcIdx, stop=srcIdx+1, label=self.label)
        return None
    def __str__(self) -> str:
        return f'{self._label}[{'^' if self.inv else ''}{''.join(self.spec)}]'

# NON-TERMINALS
class NonTerminal(ParseClause):
    spec:tuple[ParseClause, ...]
    def __init__(self, *spec:ParseClause, label='') -> None:
        self.spec = spec
        self.label = label


class Seq(NonTerminal):
    def startswith(self, child: ParseClause) -> bool:
        for n in self.spec:
            if n == child:
                return True
            if n.nullable is False:
                return n.startswith(child)

        return super().startswith(child)

    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        content = []
        i = srcIdx
        for child in self.spec:
            n = memo.get((i, child))
            if n is None:
                return None
            content.append(n)
            i = n.stop

        return ParseNode(clause=self, content=tuple(content), start=srcIdx, stop=i, label=self.label)
    def __str__(self) -> str:
        return f"{self._label}({' '.join(str(s) for s in self.spec)})"

class First(NonTerminal):
    """match the first valid clause in a list of ParseClauses"""
    def startswith(self, child: ParseClause):
        for n in 
        return any(n.couldStartWith(child) for n in self.spec)
    def mustConsumeInput(self, visited=None) -> bool:
        if visited is None:
            visited = set()
        # return all(n.mustConsumeInput() for n in self.spec)
        for n in self.spec:
            if n not in visited:
                if not n.mustConsumeInput(visited):
                    self.mustConsumeInput = finalize[False]
                    return self.mustConsumeInput()

        self.mustConsumeInput = finalize[True]
        return self.mustConsumeInput()

    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        for child in self.spec:
            n = memo.get((srcIdx, child))
            if n is not None:
                return n
        return None
    def __str__(self) -> str:
        return super().__str__() + f"({' / '.join(str(s) for s in self.spec)})"

class ZeroPlus(Seq):
    """greedily repeat a ParseClause."""
    mustConsumeInput = finalize[False]
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        content = []
        i = srcIdx
        while True:
            rcontent = []
            for child in self.spec:
                n = memo.get((i, child))
                if n is None:
                    return ParseNode(clause=self, content=tuple(content), start=srcIdx, stop=i, label=self.label)
                rcontent.append(n)
                i = n.stop
            content.extend(rcontent)
    def __str__(self) -> str:
        return super().__str__() + '*'

class Not(Seq):
    """matches if the subclause does not match. Always consumes zero characters."""
    mustConsumeInput = finalize[False]
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        n = super().match(srcIdx, src, memo)
        if n is None:
            return ParseNode(clause=self, content=(), start=srcIdx, stop=srcIdx, label=self.label)
        return None
    def __str__(self) -> str:
        label = self.label + ':' if self.label else ''
        return f"{label}!({' '.join(str(s) for s in self.spec)})"


# DERIVED PEG OPERATORS
def Follows(*spec, label=''):
    return Not(Not(*spec), label=label)

def Optional(*spec, label=''):
    return First(Seq(*spec), e, label=label)

def OnePlus(*spec, label=''):
    return Seq(*spec, ZeroPlus(*spec), label=label)

