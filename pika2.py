"""
# what is this
see also pika parsing paper: https://arxiv.org/pdf/2005.06444

# Design
This was implemented with the idea of porting it to another language half in mind, so some implmentation decisions might seem weirdly unpythonic.

comments containing '§' are referrencing sections of this paper

## clauses
rather than use classes, use only basic python types: bool, tuple, str
This is essentially emulating a tagged union, and translates very directly to a struct.


## TODO I got some questions
* document this
    * add § from paper
    * this docstring

* how does associativity shake out?
    * can we force left and right association w/o flags?
    * looks like `seq <- E E+` is right associative by default
    * how do we flag this?
    * like jon blow said, just do the wrong thing, and fix it in post


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
    * use the same grammar format and match (same base)
    * should also be able to use the same metaGrammer and toPEG
    * at least use the same base
    * use tests to show equivalence
"""
from abc import ABC, abstractmethod
from collections import defaultdict
from enum import IntEnum
import heapq
import itertools
from ast import literal_eval
from typing import NamedTuple


class clause(NamedTuple):
    """base class for parser clauses"""


# TODO use typing.NamedTuple
class T(IntEnum): # clause types
    # pseudo
    ref = 0  # name
    label = 1# label:
    # terminal
    lit = 2  # ""
    char = 3 # []
    dot = 4  # .
    # non-terminal
    seq = 5  # ' '
    first = 6# /
    no = 7   # !
    yes = 8  # &
    one = 9  # +
    zed = 10 # *
    opt = 11 # ?

type grammar = dict[str, clause]
type clause = tuple[T, *tuple[str|bool|clause,...]]

# match[label, start, stop, content]
type match = tuple[str, int, int, tuple]

type ast = tuple[str, *tuple[str|ast,...]]

# helper functions to create parsing clauses
def ref(name:str) -> clause:
    return T.ref, name
def label(name:str, clause:tuple) -> clause:
    return T.label, name, clause
def lit(value:str) -> clause:
    return T.lit, value
def char(*spec:str, invert=False) -> clause:
    assert all(len(s) <= 2 for s in spec)
    return T.char, invert, *spec
def dot(_=None) -> clause:
    return T.dot,
def seq(*spec:tuple) -> clause:
    c = []
    for x in spec:
        if x[0] == T.seq:
            c.extend(x[1:])
        else:
            c.append(x)
    return T.seq, *c
def first(*spec:tuple) -> clause:
    c = []
    for x in spec:
        if x[0] == T.first:
            c.extend(x[1:])
        else:
            c.append(x)
    return T.first, *c
def no(spec:tuple) -> clause:
    return T.no, spec
def zed(spec:tuple) -> clause:
    return T.zed, spec
def one(spec:tuple) -> clause:
    return T.one, spec
def opt(spec:tuple) -> clause:
    return T.opt, spec
def yes(spec:tuple) -> clause:
    return T.yes, spec


# helper function to make parsed nodes
# TODO eliminate this
def node(start:int, stop:int, *content: tuple, label:str='') -> match:
    return label, start, stop, content

def genParser(grammar:grammar, startClause:str):
    """
    Generate a pika parsing function given a grammar.
    """
    # TODO before any other optimization, try to normalize the rules
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

    # detect `a <- a`, which is ill-defined.
    for k,v in grammar.items():
        if v[0] == T.ref and v[1] == k:
            raise ValueError(f"rule {k} is ill-defined (rule in form `a <- a`).")

    # this will be the set of ast nodes this parser can produce
    labels = set()

    # §2.5
    # Walk all subclauses in the grammar which are reachable from the given starting rule using a depth-first search.
    # The purpose of this is to generate a topological sort of the grammar as a graph of clauses.
    # i.e. idx is a deduplicated post-order traversal of the graph.
    # While we're visiting each node, transform references to subclauses to integer indexes into idx.
    idx = []
    seen = {}
    def dfs(n):
        if n in seen:
            return seen[n]
        # Mark this node as visited.
        # We could use any unique object here, but this one is handy.
        # Ideally, this should be the index of this node in idx, but we don't know that yet.
        # Any subclauses which capture a reference to n will have to be updated once we do.
        seen[n] = n
        # to avoid updating the whole index.
        oldlen = len(idx)
        match n[0]:
            case T.ref:
                idx.append((T.ref, dfs(grammar[n[1]])))
            case T.label:
                labels.add(n[1])
                idx.append((T.label, n[1], dfs(n[2])))
            case T.seq | T.first | T.no | T.yes | T.zed | T.one | T.opt:
                idx.append((n[0], *(dfs(x) for x in n[1:])))

            case T.lit | T.char | T.dot:
                # TODO extract single characters for initial terminal passes
                idx.append(n)
        newlen = len(idx) - 1
        # Update with our actual index, now that we know it.
        seen[n] = newlen
        # finally clean up references introduced by knowing our index late
        # NOTE I believe it's correct that only references can produce cycles
        if n[0] == T.ref:
            idx[oldlen:newlen] = [
                tuple(newlen if x == n else x for x in idx)
                if n in idx else idx
                for idx in idx[oldlen:newlen]
            ]

        return newlen
    dfs(grammar[startClause])
    index = tuple(idx) # finalize

    def getMatch(src, sI, clause, memo) -> match|None:
        k, *v = clause
        m = None
        match k:
            case T.dot:
                if sI < len(src):
                    return node(sI, sI+1)
            case T.char:
                inv, *classes = v
                if sI< len(src) and inv ^ any(c[0] <= src[sI] <= c[-1] for c in classes):
                    return node(sI, sI+1)
            case T.lit:
                if src.startswith(v[0], sI):
                    return node(sI, sI+len(v[0]))
            case T.label:
                if (m := memo.get((sI, v[1]))):
                    return (v[0],) + m[1:]
            case T.ref:
                return memo.get((sI, v[0]))
            case T.seq:
                c = []
                end = sI
                for subc in v:
                    c.append(memo.get((end, subc)))
                    if c[-1] is None:
                        break
                    end = c[-1][2] # TODO .stop messy
                else:
                    return node(sI, end, *c)
            case T.first:
                for subc in v:
                    m = memo.get((sI, subc))
                    if m is not None:
                        return m
            case T.no:
                if memo.get((sI, v[0])) is None:
                    return node(sI, sI)
            case T.zed:
                c = []
                end = sI
                while (x:=memo.get((end, v[0]))) is not None:
                    c.append(x)
                    end = c[-1][2] # TODO .stop messy
                return node(sI, end, *c)
            case T.one:
                end = sI
                if (x:=memo.get((sI, v[0]))) is not None:
                    c = [x]
                    end = c[-1][2] # TODO .stop messy
                    while (x:=memo.get((end, v[0]))) is not None:
                        c.append(x)
                        end = c[-1][2] # TODO .stop messy
                    return node(sI, end, *c)
            case T.opt:
                m = memo.get((sI, v[0]))
                return node(sI, sI) if m is None else m
            case T.yes:
                if memo.get((sI, v[0])):
                    return node(sI, sI)
            case _:
                raise ValueError(f"{clause=}")

    memo = {}
    alwaysRun = []
    nullable = set()
    for cI,c in enumerate(index):
        if (m:=getMatch('', 0, c, memo)) is not None:
            # determine which clauses to always run
            # by matching them against an empty src string.
            memo[0,cI] = m
            alwaysRun.append(cI)
            nullable.add(cI)
        elif c[0] in (T.lit, T.char, T.dot):
            # also include all terminal nodes
            alwaysRun.append(cI)

    # seed parent clauses
    seeds = defaultdict(list)
    for cI,c in enumerate(index):
        match c[0]:
            case T.label:
                seeds[c[2]].append(cI)
            case T.seq:
                for child in c[1:]:
                    seeds[child].append(cI)
                    # if the child must consume input
                    # its remaining siblings cannot seed
                    # from this parent
                    if child not in nullable:
                        break

            case T.first | T.no | T.yes | T.zed | T.one | T.opt | T.ref:
                for child in c[1:]:
                    seeds[child].append(cI)

    def parse(src:str) -> match | None:
        memo:dict[tuple[int, int], match] = {}

        # TODO rather than generating the full work queue all at once
        #   can/should we generate the queue one index at a time?
        #   we could then pre-heapify alwaysRun

        # TODO don't use node() internally (in getMatch), make smaller memos
        #   memo could be memo:list[dict[int, match]] with the list index being -sI
        # match can be simplified to just memo[sI][cI] = (endIdx, *(subsI, subcI))
        # this is enough to recover the full match tree (check for labels in index[cI][0] == T.label).

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

        # some rules always need to be checked
        q = [(-sI, cI) for sI, cI in itertools.product(range(len(src)+1), alwaysRun)]
        heapq.heapify(q)
        while q:
            task = heapq.heappop(q)
            # deduplicate work
            while q and q[0] == task:
                heapq.heappop(q)
            sI, cI = task
            sI = -sI
            m = getMatch(src, sI, index[cI], memo)
            if m is None:
                continue
            # §2.8 matches must be longer than previously found matches to be preferred.
            # this checks the stop index only as a proxy to size,
            #   since we know that the start index is the same
            oldMatch = memo.get((sI, cI))
            if oldMatch is not None and m[2] <= oldMatch[2]:
                continue
            memo[sI, cI] = m

            # enqueue seed clauses
            # seeds are mostly small, so don't bother merging (that's very slow)
            for c in seeds[cI]:
                heapq.heappush(q, (-sI, c))

        goal = memo.get((0, len(index)-1))
        if goal is None:
            # §3.2 error recovery
            # Syntax errors can be defined as regions of the input that are not spanned by matches of rules of interest. Recovering after a syntax error involves finding the next match in the memo table after the end of the syntax error for any grammar
            # rule of interest: for example, a parser could skip over a syntax error to find the next complete function, statement, or expression in the input. This lookup requires O(log n) time in the length of the input if a skip list or balanced tree is used to store each row of the memo table.

            # for our purposes, I believe the clauses of interest are those with labels
            # other options include: rule definitions (ref), explicitly marking recovery points?
            # instead of 'recovering' anything, just raise ParseError and point to the problem.
            pass
        return goal


    # return parsing function
    return parse

def memoTree(src, memo, clauses):
        # TODO attempt to print a parse tree from memo like Fig.4
        matches = [(-cI, start, end, src[start:end]) for (_, cI), (_, start, end, _) in memo.items()]
        matches.sort()
        print(''.join(f" {c}" for c in src))
        for cI, g in itertools.groupby(matches, lambda x:x[0]):
            cI = -cI
            line = []
            oldEnd = -1
            for _, start, end, s in g:
                # omit empty and overlapping matches
                if not s or start < oldEnd:
                    continue
                line += [' '] * (start * 2 - len(line))
                if start != oldEnd:
                    line.append('│')
                line.extend(' '.join(s))
                line.append('│')
                oldEnd = end
            if not line:
                continue

            line += [' '] * (len(src) * 2 - len(line)+1)
            print(''.join(line), f'¦{toPEG(clauses[cI])[:20]}')

# TODO there's probably a more robust way to do this
#   there is a whole lot of complexity around char in general
transform = {
    '[':'\\[',
    ']':'\\]',
    '\n':'\\n',
    '\t':'\\t',
    '\r':'\\r',
    # this goes last
    # we make use of the fact that iteration over a dict
    # has a guaranteed order
    '\\':r'\\',
}

def toPEG(e:tuple|dict) -> str:
    """format a PEG expression using the default peg syntax"""
    match e:
        case dict():
            return '\n'.join(f"{k} <- {toPEG(v)}" for k,v in e.items())
        case tuple():
            match e[0]:
                case T.ref:
                    return e[1]
                case T.label:
                    return f"{e[1]}:{toPEG(e[2])}"
                case T.lit:
                    return repr(e[1])
                case T.char:
                    content = ['^' if e[1] else '']
                    for rule in e[2:]:
                        if len(rule) == 1:
                            content.append(rule)
                        else:
                            # assert len(rule) == 2, "T.char is malformed, but let's be permissive here"
                            content.extend((rule[0], '-', rule[-1]))
                    return f"[{''.join(transform.get(c, c) for c in content)}]"
                case T.dot:
                    return '.'
                case T.seq:
                    return f"({' '.join(toPEG(x) for x in e[1:])})"
                case T.first:
                    return f"({' / '.join(toPEG(x) for x in e[1:])})"
                case T.no:
                    return '!' + toPEG(e[1])
                case T.yes:
                    return '&' + toPEG(e[1])
                case T.zed:
                    return toPEG(e[1]) + '*'
                case T.one:
                    return toPEG(e[1]) + '+'
                case T.opt:
                    return toPEG(e[1]) + '?'
                case _:
                    raise ValueError(f"{e=}")
        case _:
            raise ValueError(f"{e=}")

G:grammar = {}
G['EOL'] = first(lit('\r\n'), lit('\n'), lit('\r'))
G['comment'] = seq(lit('#'), zed(seq(no(ref('EOL')), dot())), ref('EOL'))
G['sp'] = zed(first(lit(' '), lit('\t'), ref('EOL'), ref('comment')))
#Char <- '\\' [nrt'"\[\]\\] / '\\' [0-2][0-7][0-7] / '\\' [0-7][0-7]? / !'\\' .
ss = lit('\\')
o7 = char('07')
G['char'] = first(
    seq(ss, char(*"nrt'\"[]\\")),
    seq(ss, char('02'), o7, o7),
    seq(ss, o7, opt(o7)),
    seq(no(ss), dot()),
)
#Class <- cclass:('[' (!']' lit:(Char '-' Char / Char))* ']') sp
G['class'] =  seq(
    label('char', seq(
        lit('['), zed(seq(
            no(lit(']')),
            label('crange', first(
                seq(ref('char'), lit('-'), ref('char')),
                ref('char')
            )),
        )),
        lit(']'),
    )),
    ref('sp')
)
#Identifier <- identifier:[a-zA-Z_]+ sp
G['identifier'] = seq(label(
    'identifier',
    seq(char('az', 'AZ', '_'), zed(char('az', 'AZ', '_', '09'))),
    
), ref('sp'))
#Literal <- literal:(['] (!['] Char)* ['] / ["] (!["] Char)* ["]) sp
q = lit("'")
qq = lit('"')
G['lit'] = seq(label('lit', first(
    seq(q, zed(seq(no(q), ref('char'))), q),
    seq(qq, zed(seq(no(qq), ref('char'))),qq)
)), ref('sp'))
G['grammar'] = seq(ref('sp'), zed(ref('definition')), no(dot()))
G['definition'] = label('rule',seq(ref('identifier'), lit('<-'), ref('sp'), ref('E')))
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
# TODO extract generic fmtTree
def fmtMatch(src, n:match, *, prefix:str='', next_p=''):
    label, start, stop, content = n
    out = [
        f"{prefix}{next_p}{label}{':' if label else ''}{src[start:stop]!r}"
    ]
    match next_p:
        case '├':
            prefix += '│'
        case '└':
            prefix += ' '
    if content:
        for c in content[:-1]:
            out.append(fmtMatch(src, c, prefix=prefix, next_p='├'))
        out.append(fmtMatch(src, content[-1], prefix=prefix, next_p='└'))
    return '\n'.join(out)

def fmtAst(a:ast|str, *, prefix='', next_p=''):
    match a:
        case str():
            return f"{prefix}{next_p}{a!r}"
        case _:
            out = [f"{prefix}{next_p}{a[0]}"]
            match next_p:
                case '├':
                    prefix += '│'
                case '└':
                    prefix += ' '
            if a[1:]:
                for c in a[1:-1]:
                    out.append(fmtAst(c, prefix=prefix, next_p='├'))
                out.append(fmtAst(a[-1], prefix=prefix, next_p='└'))
            return '\n'.join(out)

def grammarFromPEG(src:str) -> grammar | None:
    if (m:=metaParser(src)) is None:
        return None
    G:grammar = {}
    def rule(name, expr):
        G[name] = expr
    def identifier(name):
        return name
    def crange(name:str):
        # TODO unescape chars
        for new, old in transform.items():
            name = name.replace(old, new)
        match len(name):
            case 1:
                return name
            case 3:
                return name[0::2]
            case _:
                raise ValueError(name)

    def char(*lit):
        inv = lit and lit[0] == '^'
        if inv:
            lit = lit[1:]
        return T.char, inv, *lit
    def lit(value):
        return T.lit, literal_eval(value)

    k = {
        func.__name__:func
        for func in [rule, identifier, crange, ref, label, lit, char, dot, seq, first, no, zed, one, opt, yes]
    }
    def toC(a):
        if isinstance(a, (str,bool)):
            return a
        func = k.get(a[0])
        if func is None:
            raise ValueError(f'unknown ast type {a[0]}')
        return func(*map(toC, a[1:]))
    for a in trim(src, m):
        toC(a)
    return G

def trim(src:str, n:match|None):
    if n is None:
        return
    if n[0]:
        content = []
        for c in n[3]:
            content.extend(trim(src, c))
        if content:
            yield n[0], *content
        else:
            yield n[0],src[n[1]:n[2]]
    else:
        for c in n[3]:
            yield from trim(src, c)


metaGrammar = toPEG(G)
metaParser = genParser(G, 'grammar')

# TODO __all__ = ['metaGrammar', 'metaParser', 'genParser']

# TESTS

def test_meta():
    """
    this is proof of the fixed point grammar.
    """
    newG = grammarFromPEG(metaGrammar)
    assert isinstance(newG, dict), 'failed to parse meta grammar'
    for k,newv in newG.items():
        oldv = G[k]
        rulePEG = f"{k} <- {toPEG(oldv)}"
        assert oldv == newv, rulePEG
    assert newG == G

def test_tbd():
    # TODO tests to implement
    # test char `[-]`
    pass

def test_fmt():
    test_node = node(0, 5, node(0,1), node(1,2, label='op'), node(2, 5, node(2, 3), node(3,4, label='op'), node(4,5), label='mul'), label='add')
    assert fmtMatch('1+2*3',test_node) == """add:'1+2*3'
├'1'
├op:'+'
└mul:'2*3'
 ├'2'
 ├op:'*'
 └'3'"""

if __name__ == "__main__":
    import pytest
    pytest.main([__file__])
