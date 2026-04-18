from pprint import pp
from collections import defaultdict
from dataclasses import dataclass
import heapq
import itertools

"""
TODO
* can/should we condense the terminal clauses to a regex?
    * could very fast sweep and put to memo before properly starting
    * could do the same for nullable clauses
* error handling, recovery?
    * can I emit parseErrors the same way as python does? with highlighting and context
* incremental parsing
    * rather than indexing the cache on the absolute index of a character,
    * store the input as a rope, then index on a node in the rope
    * when an edit occurs, invalidate and reparse only spans that cross the edit.
"""

class T: # jank enum for clause types
    # pseudo
    ref = 0
    label = 1
    # terminal
    lit = 2 # ''
    char = 3 # []
    dot = 4  # .
    # non-terminal
    seq = 5  # ' '
    first = 6# /
    no = 7   # !
    yes = 8 # &
    one = 9  # +
    zed = 10 # *
    opt = 11 # ?

# helper functions to create parsing clauses
def ref(name:str):
    return T.ref, name
def label(name:str, clause:tuple):
    return T.label, name, clause
def lit(value:str):
    return T.lit, value
def char(*spec:str, invert=False):
    return T.char, invert, *spec
def dot():
    return T.dot,
def seq(*spec:tuple):
    return T.seq, *spec
def first(*spec:tuple):
    return T.first, *spec
def no(spec:tuple):
    return T.no, spec
def zed(spec:tuple):
    return T.zed, spec
def one(spec:tuple):
    return T.one, spec
def opt(spec:tuple):
    return T.opt, spec
def yes(spec:tuple):
    return T.yes, spec


# helper function to make parsed nodes
type match = tuple[str, int, int, tuple]
def node(start:int, stop:int, *content: tuple, label:str='') -> match:
    return label, start, stop, content

class grammar(dict):
    def genParser(self, startClause:str):
        # TODO walk all clauses and subclauses to produce
        # 1. an ordered set of all subclauses
        # 2. a set of indices of parent clauses to trigger on match
        # 3. a parsing function

        # walk all clauses and subclauses reachable from the starting clause in a post order dfs
        # TODO calculate parent seed clauses, and alwaysEval to avoid evaluating every clause at every position. heapify at the end
        # terminals must be evaluated at every position.
        # take special care to handle `!.`

        # an ordered list of subclauses in the grammar.
        # Each clause is at its assigned index
        clauses = []
        # the same list of clauses, but where all subclauses
        # have been substituted out with their index
        index = []
        # dict[clause, index]
        seen = {}
        def dfs(n):
            if n in seen:
                return seen[n]
            seen[n] = None
            match n[0]:
                case T.ref:
                    index.append((T.ref, dfs(self[n[1]])))
                case T.label:
                    index.append((T.label, n[1], dfs(n[2])))
                case T.seq | T.first | T.no | T.yes | T.zed | T.one | T.opt:
                    index.append((n[0], *(dfs(x) for x in n[1:])))

                case T.lit | T.char | T.dot:
                    index.append(n)
            i = len(clauses)
            # TODO there needs to be a more extensive cleanup
            # to catch the None references introduced by seen[n]
            seen[n] = i # update reference
            clauses.append(n)
            return i
        dfs(self[startClause])

        # TODO debug
        for i, c in enumerate(clauses):
            print(i, index[i], toPEG(c))

        def getMatch(src, sI, clause, memo) -> match|None:
            k, *v = clause
            m = None
            match k:
                case T.dot:
                    if sI < len(src):
                        m = node(sI, sI+1)
                case T.char:
                    inv, *classes = v
                    # TODO this isn't very robust w/ escape chars
                    if sI< len(src) and inv ^ any(c[0] <= src[sI] <= c[-1] for c in classes):
                        m = node(sI, sI+1)
                case T.lit:
                    if src.startswith(v[0], sI):
                        m = node(sI, sI+len(v[0]))
                case T.label:
                    m = memo.get((sI, v[1]))
                    if m:
                        m = (v[0],) + m[1:]
                case T.ref:
                    m = memo.get((sI, v[0]))
                case T.seq:
                    c = []
                    end = sI
                    for subc in v:
                        c.append(memo.get((end, subc)))
                        if c[-1] is None:
                            break
                        end = c[-1][2] # TODO .stop messy
                    else:
                        m = node(sI, end, *c)
                case T.first:
                    for subc in v:
                        m = memo.get((sI, subc))
                        if m is not None:
                            break
                case T.no:
                    if memo.get((sI, v[0])) is None:
                        m = node(sI, sI)
                case T.zed:
                    c = []
                    end = sI
                    while (x:=memo.get((end, v[0]))) is not None:
                        c.append(x)
                        end = c[-1][2] # TODO .stop messy
                    m = node(sI, end, *c)
                case T.one:
                    end = sI
                    if (x:=memo.get((sI, v[0]))) is not None:
                        c = [x]
                        end = c[-1][2] # TODO .stop messy
                        while (x:=memo.get((end, v[0]))) is not None:
                            c.append(x)
                            end = c[-1][2] # TODO .stop messy
                        m = node(sI, end, *c)
                case T.opt:
                    m = memo.get((sI, v[0]))
                    if m is None:
                        m = node(sI, sI)
                case T.yes:
                    if memo.get((sI, v[0])):
                        m = node(sI, sI)
                case _:
                    raise ValueError(f"{clause=}")
            return m


        memo = {}
        alwaysRun = []
        nullable = set()
        for cI,c in enumerate(index):
            if (m:=getMatch('', 0, index[cI], memo)) is not None:
                # determine which clauses to always run
                # by matching them against an empty src string.
                memo[0,cI] = m
                alwaysRun.append(cI)
                nullable.add(cI)
            elif c[0] in (T.lit, T.char, T.dot):
                # also include all terminal nodes
                alwaysRun.append(cI)

        # TODO seed parent clauses
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

        print(f"rules={len(self)}")
        print(f"{len(index)=}")
        print(f"{len(alwaysRun)=}")
        print(f"{len(nullable)=}")
        print(f"terminals={len(alwaysRun)-len(nullable)}")
        avg_seeds = sum(map(len, seeds.values())) / len(seeds)
        print(f"{avg_seeds=}")

        def parse(src:str) -> match | None:
            memo:dict[tuple[int, int], match] = {}
            # TODO for now we are checking all possibilities
            # but this should be only the subset of clauses which must always be run
            # namely, terminal nodes, and anything which could match the empty string
            q = [(-sI, cI) for sI, cI in itertools.product(range(len(src)+1), alwaysRun)]
            heapq.heapify(q)
            while q:
                task = heapq.heappop(q)
                # deduplicate work
                while q and q[0] == task:
                    heapq.heappop(q)
                sI, cI = task
                sI = -sI
                mI = sI, cI
                m = getMatch(src, sI, index[cI], memo)
                if m is None:
                    continue
                # §2.8 matches must be longer than previously found matches to be preferred.
                # this checks the stop index only as a proxy to size,
                #   since we know that the start index is the same
                oldMatch = memo.get(mI)
                if oldMatch is not None and m[2] <= oldMatch[2]:
                    continue
                memo[mI] = m

                # enqueue seed clauses
                # seeds are mostly small, so don't bother merging
                for c in seeds[cI]:
                    heapq.heappush(q, (-sI, c))
            for sI in range(len(src)):
                cI = max(cI for cI in range(len(index)) if (sI, cI) in memo)
                m = (str(sI) + toPEG(clauses[cI]),) + memo[sI, cI][1:]
                print(fmtNode(src, m))


            pp(memo)
            return memo.get((0, len(index)-1))


        # return parsing function
        return parse
    def __str__(self) -> str:
        """format a grammar using the default peg syntax"""
        return '\n'.join(f"{k} <- {toPEG(v)}" for k,v in self.items())

def toPEG(e:tuple) -> str:
    """format a PEG expression using the default peg syntax"""
    match e[0]:
        case T.ref:
            return e[1]
        case T.label:
            return f"{e[1]}:{toPEG(e[2])}"
        case T.lit:
            return repr(e[1])
        case T.char:
            return f"[{'^' if e[1] else ''}{''.join(e[2:])}]"
        case T.dot:
            return '.'
        case T.seq:
            return f"({' '.join(toPEG(x) for x in e[1:])})"
        case T.first:
            return f"({' / '.join(toPEG(x) for x in e[1:])})"
        case T.no:
            return '!' + toPEG(e[1])
        case T.zed:
            return toPEG(e[1]) + '*'
        case T.one:
            return toPEG(e[1]) + '+'
        case T.opt:
            return toPEG(e[1]) + '?'
        case T.yes:
            return '&' + toPEG(e[1])
        case _:
            raise ValueError(f"{e=}")

G = grammar()
#EOL <- '\r\n' / '\n' / '\r'
G['EOL'] = first(lit(r'\r\n'), lit(r'\n'), lit(r'\r'))
#Comment <- '#' (!EOL .)* EOL
G['comment'] = seq(lit('#'), zed(seq(no(ref('EOL')), dot())), ref('EOL'))
#sp <- (' ' / '\t' / EOL / Comment)*
G['sp'] = zed(first(lit(' '), lit(r'\t'), ref('EOL'), ref('comment')))
#Char <- '\\' [nrt'"\[\]\\] / '\\' [0-2][0-7][0-7] / '\\' [0-7][0-7]? / !'\\' .
ss = lit(r'\\')
o7 = char('0-7')
G['char'] = first(seq(ss, char(*"nrt'\"[]\\")), seq(ss, char('0-2'), o7, o7), seq(ss, o7, opt(o7)),)
#Class <- cclass:('[' (!']' string:(Char '-' Char / Char))* ']') sp
G['class'] =  seq(
    label('char', seq(
        lit('['), zed(seq(no(lit(']')), label('lit', first(seq(ref('char'), lit('-'), ref('char')), ref('char'))), )),
        lit(']'),
    )),
    ref('sp')
)
#Identifier <- identifier:[a-zA-Z_]+ sp
G['identifier'] = seq(label('identifier', one(char('a-z', 'A-Z', '_'))), ref('sp'))
#Literal <- literal:(['] (!['] Char)* ['] / ["] (!["] Char)* ["]) sp
q = lit("'")
qq = lit('"')
G['literal'] = seq(label('literal', first(
    seq(q, zed(seq(no(q), ref('char'))), q),
    seq(qq, zed(seq(no(qq), ref('char'))),qq)
)), ref('sp'))
#Grammar <- sp Definition+ !.
G['grammar'] = seq(ref('sp'), zed(ref('definition')), no(dot()))
#Definition <- rule:(Identifier '<-' sp E)
G['definition'] = label('rule',seq(ref('identifier'), lit('<-'), ref('sp'), ref('E')))
#E <- ruleref:Identifier !'<-' / '(' sp E ')' sp / Literal / Class / dot:'.' sp
#    / optional:(E '?' sp) / zeroplus:(E '*' sp) / oneplus:(E '+' sp)
#    / lookahead:('&' sp E) / notlookahead:('!' sp E) / label:(Identifier ':' E)
#    / seq:(E+)
#    / first:(E ('/' sp E)+)
#
G['E'] = first(
    label('opt', seq(ref('E'), lit('?'), ref('sp'))),
    label('zed', seq(ref('E'), lit('*'), ref('sp'))),
    label('one', seq(ref('E'), lit('+'), ref('sp'))),
    label('yes', seq(lit('&'), ref('sp'), ref('E'))),
    label('no',seq(lit('!'), ref('sp'), ref('E'))),
    label('label',seq(ref('identifier'), lit(':'), ref('sp'), ref('E'))),
    label('seq', seq(ref('E'), one(ref('E')))),
    label('first',seq(ref('E'), one(seq(lit('/'), ref('sp'), ref('E'))))),
    label('ref',seq(ref('identifier'), no(lit('<-')))),
    seq(lit('('), ref('sp'), ref('E'), lit(')'), ref('sp')),
    ref('literal'),
    ref('class'),
    label('dot', seq(lit('.'), ref('sp'))),
)


def fmtNode(src, n:match, *, prefix:str='', next_p=''):
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
            out.append(fmtNode(src, c, prefix=prefix, next_p='├'))
        out.append(fmtNode(src, content[-1], prefix=prefix, next_p='└'))
    return '\n'.join(out)

def test_fixedpoint():
    newG = grammarFromAst(metaParser(str(G)))
    assert  G == newG

def test_fmt():
    test_node = node(0, 5, node(0,1), node(1,2, label='op'), node(2, 5, node(2, 3), node(3,4, label='op'), node(4,5), label='mul'), label='add')
    assert fmtNode('1+2*3',test_node) == """add:'1+2*3'
├'1'
├op:'+'
└mul:'2*3'
 ├'2'
 ├op:'*'
 └'3'"""
    assert False, "write tests for str(grammar)"

def trim(src:str, n:match):
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


#print(G)
metaGrammar = str(G)
metaParser = G.genParser('grammar')

#exit()
def pparse(src:str, parser=metaParser):
    m = parser(src)
    if m is None:
        print('failed')
    else:
        print(fmtNode(src, m))
        print('trimmed')
        for n in trim(src, m):
            pp(n)

pparse('a <- a b <- a')
