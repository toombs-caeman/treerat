import itertools
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache, cached_property
from collections import defaultdict
from typing import Callable, Generator, Hashable, Self
from base import Parser, ParseError
import graphlib
import heapq

# see also pika parsing paper: https://arxiv.org/pdf/2005.06444
# comments containing '§' are referrencing sections of this paper

__all__ = [
    'PikaParser', # type
    'PikaMetaParser', # isinstance(PikaParser)
    'generateParser', # def (grammar:str) -> PikaParser
    'ParseError', # Exception
]

type memo = dict[tuple[int, ParseClause], ParseNode]
# BASE TYPES
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

finalize = [lambda s=None,v=None: False, lambda s=None,v=None: True]

class ParseClause(ABC):
    label: str = ''
    spec = None
    @abstractmethod
    def match(self, srcIdx:int, src: str, memo:memo) -> ParseNode | None:
        """either produce a node or fail to match."""

    def __hash__(self) -> int:
        return hash(str(self))

    def __eq__(self, value):
        return type(self) == type(value) and self.spec == value.spec

    @abstractmethod
    def mustConsumeInput(self, visited=None) -> bool:
        """Return True iff this clause must consume at least one character to match."""

    @abstractmethod
    def couldStartWith(self, child:ParseClause) -> bool:
        """Return True iff, a match of this clause could start at the same position as a match of the child clause."""

    @abstractmethod
    def withLabel(self, label:str) -> Self:
        """return a copy of this clause with the given label"""
    def __str__(self) -> str:
        return self.label + ':' if self.label else ''

class Terminal(ParseClause):
    def couldStartWith(self, child: ParseClause) -> bool:
        return self == child

class String(Terminal):
    def __init__(self, spec:str, *, label='') -> None:
        self.spec = spec
        self.label = label
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        if not src.startswith(self.spec, srcIdx):
            return None
        return ParseNode(clause=self, content=(), start=srcIdx, stop=srcIdx+len(self.spec), label=self.label)
    def mustConsumeInput(self, visited=None) -> bool:
        self.mustConsumeInput = finalize[bool(self.spec)]
        return self.mustConsumeInput()
    def withLabel(self, label: str) -> Self:
        return type(self)(self.spec, label=label)
    def __str__(self) -> str:
        return super().__str__() + repr(self.spec)

class CClass(Terminal):
    def __init__(self, *spec:str, label='') -> None:
        self.inv = spec[0] == '^'
        self.spec = spec[1:] if self.inv else spec
        self.label = label
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        if srcIdx < len(src) and self.inv ^ any(
            r[0] <= src[srcIdx] <= r[-1] for r in self.spec
        ):
            return ParseNode(
                clause=self,
                content=(),
                start=srcIdx,
                stop=srcIdx+1,
                label=self.label
            )
        return None
    mustConsumeInput = finalize[True]
    def withLabel(self, label: str) -> Self:
        return type(self)(*self.spec, label=label)
    def __str__(self) -> str:
        inner = ''.join(self.spec)
        inv = '^' if self.inv else ''
        return f'{super().__str__()}[{inv}{inner}]'

class Dot(Terminal):
    def __init__(self, *, label='') -> None:
        self.label = label
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        if srcIdx < len(src):
            return ParseNode(clause=self, content=(), start=srcIdx, stop=srcIdx+1, label=self.label)
        return None
    mustConsumeInput = finalize[True]
    def withLabel(self, label: str) -> Self:
        return type(self)(label=label)
    def __str__(self) -> str:
        return super().__str__() + '.'

class NonTerminal(ParseClause):
    spec:tuple[ParseClause, ...]
    def __init__(self, *spec:ParseClause, label='') -> None:
        self.spec = spec
        self.label = label
    def withLabel(self, label: str) -> Self:
        return type(self)(*self.spec, label=label)

# CORE PEG OPERATORS
class Seq(NonTerminal):
    """match a sequence of ParseClauses"""
    def couldStartWith(self, child: ParseClause):
        for n in self.spec:
            if n == child:
                return True
            if n.mustConsumeInput():
                return n.couldStartWith(child)
        return False
    def mustConsumeInput(self, visited=None) -> bool:
        if visited is None:
            visited = set()
        # return any(n.mustConsumeInput() for n in self.spec)
        for n in self.spec:
            if n not in visited:
                visited.add(n)
                if n.mustConsumeInput(visited):
                    self.mustConsumeInput = finalize[True]
                    return self.mustConsumeInput()
        self.mustConsumeInput = finalize[False]
        return self.mustConsumeInput()

    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        content = []
        i = srcIdx
        for child in self.spec:
            while isinstance(child, RuleRef):
                child = child.rule
            n = memo.get((i, child))
            if n is None:
                return None
            content.append(n)
            i = n.stop

        return ParseNode(clause=self, content=tuple(content), start=srcIdx, stop=i, label=self.label)
    def __str__(self) -> str:
        return super().__str__() + f"({' '.join(str(s) for s in self.spec)})"

class First(NonTerminal):
    """match the first valid clause in a list of ParseClauses"""
    def couldStartWith(self, child: ParseClause):
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
            while isinstance(child, RuleRef):
                child = child.rule
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
                while isinstance(child, RuleRef):
                    child = child.rule
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

# DERIVED PEG TERMINALS
dot = CClass('^') # matches any one character
e = String('') # matches the empty string




class PikaParser:
    """
    """
    def __init__(self, startNode:ParseClause | grammar):
        if isinstance(startNode, grammar):
            startNode = startNode.rules[startNode.startRule]
        while isinstance(startNode, RuleRef):
            startNode = startNode.rule # dereference
        # construct clause graph.
        # this SHOULD deduplicate nodes by hash
        self.alwaysEval: set[ParseClause] = set()
        graph = defaultdict(set) # dict[child, iterable[parent]]
        # topo sort for priority §2.5
        counter = itertools.count()
        # §2.5 deduplicated post order traversal, starting at the starting rule,
        # breaking cycles where a node is visited again
        self.clauseIdx: dict[ParseClause, int] = {}
        def walk(n:ParseClause):
            if n in self.clauseIdx:
                # we've already visited this node.
                return
            # record that we've visited this node
            self.clauseIdx[n] = 0
            if not n.mustConsumeInput():
                self.alwaysEval.add(n)
            #print(f"walk {str(n)}")
            match n:
                case Terminal():
                    # these must always be evaluated because
                    # there's no better way to know if the rule should be triggered
                    # than to just match it.
                    self.alwaysEval.add(n)
                case NonTerminal():
                    for child in n.spec:
                        while isinstance(child, RuleRef):
                            child = child.rule # dereference
                        graph[child].add(n)
                        walk(child)
                case _:
                    raise Exception(type(n))
            # update index in post-order
            self.clauseIdx[n] = next(counter)
        # by only walking the start node, rather than every rule in the grammar,
        # we automatically trim the grammar to reachable nodes
        walk(startNode)

        self.startNode = startNode

        # for each clause, get a list of parent seed clauses
        self.seedClauses: dict[ParseClause, list[ParseClause]] = defaultdict(list)
        for child, parents in graph.items():
            self.seedClauses[child] = [parent for parent in parents if parent.couldStartWith(child)]

        # these clauses must always be evaluated at each position
        # because they could consume no input.
        for clause in self.clauseIdx:
            if not clause.mustConsumeInput():
                self.alwaysEval.add(clause)
        for p in graph[String(' ')]:
            print(p)
        for p in self.seedClauses[String(' ')]:
            print(p)


    def __call__(self, src:str) -> ParseNode | None:
        memo: memo = {}
        q:list[tuple[int, int, ParseClause]] = [
            (-srcIdx, self.clauseIdx[clause], clause)
            for srcIdx in range(len(src) + 1)
            for clause in self.clauseIdx
            # TODO we shouldn't have to always evaluate every clause
        ]
        heapq.heapify(q)
        print(f"{len(src)=}")
        while q:
            item = heapq.heappop(q)
            while q and item[:2] == q[0][:2]:
                # it is possible for duplicate work to be enqueued
                # the duplicate work will always be sequential,
                heapq.heappop(q)
            srcIdx, cI, clause = item
            srcIdx = -srcIdx
            mIdx = srcIdx, clause

            node = clause.match(srcIdx, src, memo)
            if node is None:
                #print(f"{srcIdx} None {cI:>50}:{str(clause)}")
                continue
            if node.start != node.stop:
                print(f"[{node.start}:{node.stop}] {repr(src[node.start:node.stop])if srcIdx < len(src) else '⊥':<{len(src)}} {cI:>30}:{str(clause)} ")
                pass
            #print(srcIdx, isinstance(clause, Terminal), clause, node)
            # TODO There is one exception to this:
            #   for First clauses, even before the length of the new match is checked against the length of the existing match as described above, the index of the matching subclause of each match must be compared, since the semantics of the First PEG operator require that an earlier matching subclause take priority over a later matching subclause 
            # §2.8 matches must be longer than previously found matches to be preferred.
            if mIdx in memo and node.stop <= memo[mIdx].stop:
                print(f"dropping duplicate {mIdx}")
                continue
            # §2.6
            memo[mIdx] = node
            for seed in self.seedClauses[clause]:
                heapq.heappush(q, (-srcIdx, self.clauseIdx[seed], seed))
        return memo.get((0, self.startNode), None)

# modified from https://bford.info/pub/lang/peg.pdf
meta_grammar = r"""
# Hierarchical syntax
Grammar <- sp Definition+ !.
Definition <- rule:(Identifier '<-' sp E)
E <- ruleref:Identifier !LEFTARROW / '(' sp E ')' sp / Literal / Class / dot:'.' sp
    / optional:(E '?' sp) / zero_or_more:(E '*' sp) / one_or_more:(E '+' sp)
    / lookahead:('&' sp E) / notlookahead:('!' sp E) / label:(Identifier ':' E)
    / seq:(E+)
    / first:(E ('/' sp E)+)

# Lexical syntax
Identifier <- identifier:[a-zA-Z_]+ sp
Literal <- literal:(['] (!['] Char)* ['] / ["] (!["] Char)* ["]) sp
Class <- cclass:('[' (!']' string:(Char '-' Char / Char))* ']') sp
Char <- '\\' [nrt'"\[\]\\]
    / '\\' [0-2][0-7][0-7]
    / '\\' [0-7][0-7]?
    / !'\\' .
sp <- (' ' / '\t' / EOL / Comment)*
Comment <- '#' (!EOL .)* EOL
EOL <- '\r\n' / '\n' / '\r'
"""
class grammar:
    def __init__(self, startRule:str):
        self.startRule = startRule
        self.rules: dict[str, ParseClause] = {}
    def __getitem__(self, key:str) -> RuleRef:
        return RuleRef(key, self)
    def __setitem__(self, key, value:ParseClause):
        self.rules[key] = value
    def __str__(self) -> str:
        return '\n'.join(f"{k} <- {v}" for k,v in self.rules.items())

class RuleRef(ParseClause):
    def __init__(self, name:str, grammar:grammar):
        self.name = name
        self.grammar = grammar
    @property
    def rule(self) -> ParseClause:
        return self.grammar.rules[self.name]
    def match(self, srcIdx: int, src: str, memo: memo) -> ParseNode | None:
        return self.rule.match(srcIdx, src, memo)

    def couldStartWith(self, child: ParseClause) -> bool:
        return self.rule.couldStartWith(child)

    def mustConsumeInput(self, visited=None) -> bool:
        return self.rule.mustConsumeInput(visited)
    def withLabel(self, label: str):
        return self.rule.withLabel(label)
    def __str__(self) -> str:
        return self.name
    def __hash__(self) -> int:
        return hash(self.name)

def traverse(start:ParseClause):
    seen = set()
    def dfs(n):
        while isinstance(n, RuleRef):
            n = n.rule
        if n in seen:
            return
        seen.add(n)
        yield n
        if isinstance(n, NonTerminal):
            for child in n.spec:
                yield from dfs(child)
    return dfs(start)

G = grammar('grammar')
#EOL <- '\r\n' / '\n' / '\r'
G['EOL'] = First(String(r'\r\n'), String(r'\n'), String(r'\r'))
#Comment <- '#' (!EOL .)* EOL
G['comment'] = Seq(String('#'), ZeroPlus(Not(G['EOL']), Dot()), G['EOL'])
#sp <- (' ' / '\t' / EOL / Comment)*
G['sp'] = ZeroPlus(First(String(' '), String(r'\t'), G['EOL'], G['comment']))
#Char <- '\\' [nrt'"\[\]\\] / '\\' [0-2][0-7][0-7] / '\\' [0-7][0-7]? / !'\\' .
ss = String(r'\\')
o7 = CClass('0-7')
G['char'] = First(Seq(ss, CClass(*"nrt'\"[]\\")), Seq(ss, CClass('0-2'), o7, o7), Seq(ss, o7, Optional(o7)),)
#Class <- cclass:('[' (!']' string:(Char '-' Char / Char))* ']') sp
G['class'] =  Seq(
    Seq(
        String('['),
        ZeroPlus(
            Not(String(']')),
            First(Seq(G['char'], String('-'), G['char']), G['char'], label='string'),
        ),
        String(']'),
        label='cclass'
    ),
    G['sp']
)
#Identifier <- identifier:[a-zA-Z_]+ sp
G['identifier'] = Seq(OnePlus(CClass('a-z', 'A-Z', '_'), label='identifier'), G['sp'])
# TODO
#Literal <- literal:(['] (!['] Char)* ['] / ["] (!["] Char)* ["]) sp
q = String("'")
qq = String('"')
G['literal'] = Seq(First(
    Seq(q, ZeroPlus(Not(q), G['char']),q),
    Seq(qq, ZeroPlus(Not(qq), G['char']),qq),
    label='literal'
), G['sp'])
#Grammar <- sp Definition+ !.
G['grammar'] = Seq(G['sp'], OnePlus(G['definition']), Not(Dot()))
#Definition <- rule:(Identifier '<-' sp E)
G['definition'] = Seq(G['identifier'], String('<-'), G['sp'], G['E'], label='rule')
#E <- ruleref:Identifier !'<-' / '(' sp E ')' sp / Literal / Class / dot:'.' sp
#    / optional:(E '?' sp) / zeroplus:(E '*' sp) / oneplus:(E '+' sp)
#    / lookahead:('&' sp E) / notlookahead:('!' sp E) / label:(Identifier ':' E)
#    / seq:(E+)
#    / first:(E ('/' sp E)+)
#
G['E'] = First(
    Seq(G['E'], String('?'), G['sp'], label='optional'),
    Seq(G['E'], String('*'), G['sp'], label='zeroplus'),
    Seq(G['E'], String('+'), G['sp'], label='oneplus'),
    Seq(String('&'), G['sp'], G['E'], label='lookahead'),
    Seq(String('!'), G['sp'], G['E'], label='notlookahead'),
    Seq(G['identifier'], String(':'), G['sp'], G['E'], label='label'),
    OnePlus(G['E'], label='seq'),
    Seq(G['E'], OnePlus(String('/'), G['sp'], G['E']), label='first'),
    # terminals
    Seq(G['identifier'], Not(String('<-')), label='ruleref'),
    Seq(String('('), G['sp'], G['E'], String(')'), G['sp']),
    G['literal'], G['class'], Seq(String('.', label='dot'), G['sp']),
)

PikaMetaParser = PikaParser(G)

def generateParser(grammar:str) -> PikaParser:
    metaAST = PikaMetaParser(grammar)
    if metaAST is None:
        raise Exception("didn't cleanly parse grammar")
    print(metaAST.format())
    metaAST = metaAST.clean()
    if metaAST is None:
        raise Exception("didn't specify any labels?")
    # metaAST.cast({
    #     'optional',
    #     'zeroplus',
    #     'oneplus',
    #     'lookahead',
    #     'notlookahead',
    #     'label',
    #     'first',
    #     'seq',
    #     'ruleref',
    # })
    #

if __name__ == "__main__":
    test_grammar = "thing <- quark thing"
    from pprint import pp
    startNode = PikaMetaParser.startNode
    # print(f'{startNode=!s}')
    # print('clauseIdx', end='=')
    # pp({str(k):v for k,v in PikaMetaParser.clauseIdx.items()})
    # print('seedClauses', end='=')
    # pp({str(k):[str(x) for x in v] for k,v in PikaMetaParser.seedClauses.items()})
    
    #print(G)
    #q = G['sp']
    #print(type(q).__name__, q, q.couldStartWith(String(' ')))
    cI = sorted([(i,c.mustConsumeInput(), c in PikaMetaParser.alwaysEval, str(c)) for c, i in PikaMetaParser.clauseIdx.items()])
    pp(cI)
    generateParser(test_grammar)
    nd = Not(String('<-'))

    print(nd in PikaMetaParser.alwaysEval)
