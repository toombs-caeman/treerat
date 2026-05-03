"""
# what is this
see also pika parsing paper: https://arxiv.org/pdf/2005.06444

# Design
This was implemented with the idea of porting it to another language in mind,
so some implmentation decisions might seem weirdly unpythonic.

comments containing '§' are referrencing sections of this paper

## clauses
rather than use classes, use only basic python types: bool, tuple, str
This is essentially emulating a tagged union,
and translates very directly to a struct.


## TODO I got some questions
* document this
    * add § from paper
    * this docstring

* how does associativity shake out?
    * can we force left and right association w/o flags?
    * looks like `seq <- E E+` is right associative by default
    * how do we flag this?
    * like jon blow said, just do the wrong thing, and fix it in post


* stats, how many tests per position vs total clauses
* terminal optimization
* can we implement a relatively efficient regex parser
    * probably don't need to with the terminals optimization

* error handling, recovery?
    * exception types
    * how do we give meaningful information about where the parse failed?
    * can I emit parseErrors the same way as python does? with highlighting and context

* incremental parsing
    * rather than indexing the cache on the absolute index of a character,
    * store the input as a rope, then index on a node in the rope
    * when an edit occurs, invalidate and reparse only spans that cross the edit.

* unify with packrat parser
    * use grammar.py
    * use the same grammar format and match (same base)
    * should also be able to use the same metaGrammer and toPEG
    * at least use the same base
    * use tests to show equivalence
"""
from collections import defaultdict
from enum import IntEnum
import heapq

from base import ParseError, Parser, match
from grammar import *

# types for internal index format

type _memo = defaultdict[int, dict[int, match]]


class Pika:
    def __init__(self, g: Grammar | str | None = None, startRule: str = 'grammar'):
        match g:
            case str():
                g = Grammar.from_ast(Pika().parse(g).ast(g))
            case None:
                g = Grammar.meta()
            case dict():
                g = Grammar(g)  # copy
            case _:
                raise ValueError(g)

        # TODO before any other optimization, try to normalize the rules
        # structural pattern matching?
        #   use a copy of grammar
        # [^] -> .
        # ![abc] . -> [^abc]
        # 'a'/'b' -> [ab]
        # 'a' 'b' -> 'ab'
        # [caab] -> [abc] -> [a-c]
        # !!a -> &a
        # a+ -> a a*
        # a? -> a / ''
        # a (b c) -> a b c
        # a/(b/c) -> a/b/c
        # references can always be eliminated unless recursive. careful

        g.deduplicate() # reduce identical subgraphs
        g.validate()
        self.grammar = g
        self.startRule = startRule

        # this will be the set of ast nodes this parser can produce
        labels = set()

        # §2.5
        # Walk all subclauses in the grammar which are reachable from the given starting rule using a depth-first search.
        # The purpose of this is to generate a topological sort of the grammar as a graph of clauses.
        # i.e. idx is a deduplicated post-order traversal of the graph.
        # While we're visiting each node, transform references to subclauses to integer indexes into idx.
        idx: list[tuple[T, *tuple[int, ...]]] = []
        metadata = {}
        seen = {}
        def getcI(n):
            return seen[id(n)]

        for cI, n in enumerate(g.terms(startRule)):
            seen[id(n)] = cI
        for cI, n in enumerate(g.terms(startRule)):
            match n:
                case [T.ref, name]:
                    idx.append((T.ref, getcI(g[name])))
                case [T.label, name, inner]:
                    labels.add(name)
                    metadata[cI] = name
                    idx.append((T.label, getcI(inner)))
                case [T.seq | T.first, left, right]:
                    idx.append((n[0], getcI(left), getcI(right)))
                case [T.no | T.yes | T.zed | T.one | T.opt, inner]:
                    idx.append((n[0], getcI(inner)))
                case [T.lit, inner]:
                    # TODO insert virtual clauses as dependency for multichar lit()
                    # basically this is a transform 'abc' -> &'a' 'abc'
                    # we do this so that lit() can be treated as a non-terminal in the multicharacter case
                    metadata[cI] = inner
                    idx.append((T.lit,))
                case [T.dot]:
                    idx.append((T.dot,))
                case [ T.char | T.ichar , *spec]:
                    # expand and deduplicate character set
                    metadata[cI] = frozenset(
                        chr(c)
                        for s in spec
                        for c in range(ord(s[0]), ord(s[-1]) + 1)
                    )
                    idx.append((n[0],))
                case _:
                    raise ValueError(n)
        # finalize
        self.index = tuple(idx)
        self.labels = frozenset(labels)
        self.metadata = metadata

        memo: _memo = defaultdict(dict)
        alwaysRun = []
        nullable = set()
        for cI, c in enumerate(self.index):
            if (m := self._match('', 0, cI, memo)) is not None:
                # determine which clauses to always run
                # by matching them against an empty src string.
                memo[0][cI] = m
                alwaysRun.append(cI)
                nullable.add(cI)
            elif c[0] in (T.lit, T.char, T.dot):
                # also include all terminal nodes
                alwaysRun.append(cI)
        heapq.heapify(alwaysRun)
        self.alwaysRun = tuple(alwaysRun)

        # §2.6
        # generate seed parent clauses
        # basically, if a clause matches, which
        seeds = [[] for _ in range(len(self.index))]
        for cI, c in enumerate(self.index):
            match c[0]:
                case T.seq:
                    for child in c[1:]:
                        seeds[child].append(cI)
                        # if the child must consume input
                        # its remaining siblings cannot seed
                        # from this parent
                        if child not in nullable:
                            break

                case T.first | T.no | T.yes | T.zed | T.one | T.opt | T.ref | T.label:
                    for child in c[1:]:
                        seeds[child].append(cI)
        # finalize seeds
        self.seeds = tuple(tuple(s) for s in seeds)

    def _match(self, src: str, sI: int, cI: int, memo: _memo) -> match | None:
        c = self.index[cI]
        match c[0]:
            case T.dot:
                if sI < len(src):
                    return match(sI, sI+1)
            case T.char | T.ichar:
                inv = c[0] == T.ichar
                spec = self.metadata[cI]
                if sI < len(src) and inv ^ (src[sI] in spec):
                    return match(sI, sI+1)
            case T.lit:
                s = self.metadata[cI]
                if src.startswith(s, sI):
                    return match(sI, sI+len(s))
            case T.label:
                if (m := memo[sI].get(c[1])):
                    return m._replace(label=self.metadata[cI])
            case T.ref:
                return memo[sI].get(c[1])
            case T.seq:
                content = []
                stop = sI
                for subc in c[1:]:
                    if (m := memo[stop].get(subc)) is None:
                        break
                    content.append(m)
                    stop = m.stop
                else:
                    return match(sI, stop, content=tuple(content))
            case T.first:
                for subc in c[1:]:
                    m = memo[sI].get(subc)
                    if m is not None:
                        return m
            case T.no:
                if memo[sI].get(c[1]) is None:
                    return match(sI, sI)
            case T.yes:
                if memo[sI].get(c[1]):
                    return match(sI, sI)
            case T.opt:
                return memo[sI].get(c[1], match(sI, sI))
            case T.zed | T.one:
                stop = sI
                content = []
                while (m := memo[stop].get(c[1])):
                    if stop == m.stop:
                        break
                    content.append(m)
                    stop = m.stop
                if content or c[0] == T.zed:
                    return match(sI, stop, content=tuple(content))
            case _:
                raise ValueError(f"{c=}")

    def parse(self, text: str) -> match:
        memo = self.get_memo(text)

        goal = memo[0].get(len(self.index)-1)
        if goal is None:
            # §3.2 error recovery
            # Syntax errors can be defined as regions of the input that are
            # not spanned by matches of rules of interest.
            # Recovering after a syntax error involves finding the next match
            # in the memo table after the end of the syntax error for any
            # rule of interest: for example, a parser could skip over a syntax
            # error to find the next complete function, statement,
            # or expression in the input. This lookup requires O(log n) time in
            # the length of the input if a skip list or balanced tree is used
            # to store each row of the memo table.

            # for our purposes, I believe the clauses of interest are labels
            # explicitly marked recovery points?
            # instead of 'recovering' anything, just raise ParseError

            # cI of labels
            of_interest = [
                i for i, c in enumerate(self.index) if c[0] == T.label
            ]

            # record the first span that has no matches in of_interest
            # TODO actually look at all labelled matches, and do interval math
            start = None
            stop = None
            sI = 0
            while sI <= len(text):
                newI = sI
                for cI in of_interest:
                    if m := memo[sI].get(cI):
                        newI = max(newI, m.stop)
                if newI == sI:
                    start = sI
                    break
                else:
                    sI = newI
            sI += 1

            while sI <= len(text):
                for cI in of_interest:
                    if m := memo[sI].get(cI):
                        stop = sI
                        break
                else:
                    sI += 1
                    continue
                break

            if stop is None:
                stop = len(text)

            def pos(idx):
                lineno = 1 + text.count('\n', 0, idx)
                offset = idx - text.rfind('\n', 0, idx)
                return lineno, offset

            startp = pos(start)
            stopp = pos(stop)
            raise ParseError(
                f'parse failed from {startp} to {stopp}',
                # file, lineno, offset, text, endlno, endoff
                (None, *startp, text, *stopp)
            )

        return goal

    def ast(self, text: str):
        return self.parse(text).ast(text)

    def get_memo(self, text: str) -> _memo:
        # TODO we could allocate this all at once
        #   almost every sI will have at least one match
        # memo:_memo = [{} for _ in range(len(text)+1)]
        memo: _memo = defaultdict(dict)

        # TODO can/should we condense the terminal clauses to a regex?
        #   this pre-check would happen here.
        #   could check any single character with a single lookup
        #   could expand character ranges, so all T.char become non-terminals
        #   add single character lookups as seeds for longer T.lit, still use startswith though
        #   dot probably requires special lookups still
        #   inverted T.char won't work well with this, probably separate that out.
        #   take special care to handle `!.`

        # TODO nullable clauses can also be initialized with an empty string match
        #   this will automatically be overridden with longer match from seed if needed

        for sI in reversed(range(len(text)+1)):
            # q is our priority queue. it is kept sorted with heapq
            # self.alwaysRun was pre-heapified
            q = list(self.alwaysRun)
            while q:
                cI = heapq.heappop(q)
                # deduplicate work
                # this will happen often, because a parent will be seeded by all of its subclauses
                while q and q[0] == cI:
                    heapq.heappop(q)
                m = self._match(text, sI, cI, memo)
                if m is None:
                    continue
                # §2.8 matches must be longer than previously found matches to be preferred.
                # this checks the stop index only, since we know that the start index is the same
                oldMatch = memo[sI].get(cI)
                if oldMatch is not None and m.stop <= oldMatch.stop:
                    continue
                memo[sI][cI] = m

                # seed parent clauses
                # seeds are mostly small, so don't bother with heapq.merge, it's very slow.
                for c in self.seeds[cI]:
                    heapq.heappush(q, c)

        return memo

    def chart(self, text: str, max_width=120, labels_only=False):
        """returns a diagram representing a parsed input."""
        # TODO upgrade to show spans and overlapping matches
        memo = self.get_memo(text)
        text = text.replace('\n', '↩')
        lines = [f"{text}─╮"]
        for cI, c in enumerate(self.grammar.terms(self.startRule)):
            if labels_only and c[0] != T.label:
                continue
            line = []
            for sI in range(len(text)+1):
                m = memo[sI].get(cI)
                if m is None:
                    marker = ' '
                else:
                    marker = '□' if m.stop == sI else '■'
                line.append(marker)
            line.append('│')
            line.append(self.grammar.pe(c))
            lines.append(''.join(line))
        lines.append(f"{text}─╯")
        return '\n'.join(line[:max_width] for line in lines)

    def spans(self, text: str, max_width=120):
        memo = self.get_memo(text)
        text = text.replace('\n', '↩')
        lines = [f"{text}─╮"]
        for cI, c in enumerate(self.grammar.terms(self.startRule)):
            if c[0] != T.label:
                continue
            spans = defaultdict(lambda: [False, False, False])
            # get all the matches of this type
            # for each position, record if a match start, stops, or spans that position.
            for sI in range(len(text) + 1):
                if m := memo[sI].get(cI):
                    spans[m.start][0] = True
                    spans[m.stop-1][2] = True
                    for i in range(m.start+1, m.stop):
                        spans[i][1] = True
            line = []
            for sI in range(len(text) + 1):
                match spans[sI]:
                    case [True, _, False]:
                        line.append('←')
                    case [False, _, True]:
                        line.append('→')
                    case [True, _, True]:
                        line.append('⟷')
                    case [_, True, _]:
                        line.append('-')
                    case _:
                        line.append(' ')
            line.append('│')
            line.append(self.grammar.pe(c))
            lines.append(''.join(line))

        lines.append(f"{text}─╯")
        return '\n'.join(line[:max_width] for line in lines)


def test_meta():
    """this is proof of the fixed point grammar."""
    defined = Grammar.meta()
    src = defined.peg()
    ast = list(Pika(defined).parse(src).ast(src))
    calc = Grammar.from_ast(ast)
    print(ast)
    assert defined.peg() == calc.peg()


def test_proto():
    pass # assert isinstance(Pika(), Parser)


if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
