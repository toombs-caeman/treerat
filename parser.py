import enum
from functools import cache, wraps


#__all__ = ['BuildParser', 'T']

"""
'specs' are a function serialized into a lisp-like syntax object.
Each function call is a list with the first element being an enum T that indicates the function, followed by string and spec arguments to curry that function with.

This allows a spec to be valid json.

"""


# the types recognized in spec
T = enum.Enum('T', (
    'Dot',
    'String',
    'CharClass',

    'Choice',
    'Sequence',

    'ZeroOrOne',
    'ZeroOrMore',
    'OneOrMore',

    'Lookahead',
    'NotLookahead',

    'Argument',
    'Index',
    'Node',
    'Label',
))

"""
all types ∈ T behave as they do in any PEG (parsing expression grammar) except Argument, Index, Node and Label.

Argument marks a section of the parsing expression to be used by a Label or Node.

Labels either return a string (if their arguments are all strings) or a flat list of nodes and strings (if any argument is a node)
Index is syntax sugar that makes it easier to define operator priority, but is otherwise equivalent to a label.

Nodes return a new node with a flat list of the given arguments.

"""
# Command names
C = enum.Enum('C', (
    'Entrypoint',
    'Definition',
    'Clear',
))

class Parser:
    def __init__(self, Entrypoint, **labels):
        """Initialize the parser according the parsing spec"""
        raise NotImplementedError
    def parse(self, text:str):
        """parse text into a parse tree"""
        raise NotImplementedError
    def fmt(self, tree) -> str:
        """
        Produces a string that would parse to the given tree with this parser.

        This is not necessarily the exact string that was used to generate the tree.
        """
        raise NotImplementedError

def BuildParser(Entrypoint, **labels) -> Parser:
    # depending on the spec, more efficent parsers could potentially be generated
    # but for now, always return a packrat
    return PackratParser(Entrypoint, **labels)


class PackratParser(Parser):
    def __init__(self, Entrypoint, **labels):
        # TODO do we have totally separate trim behaviors between labels and nodes?
        # does it make sense to have to separate definitions, even if they're structurally similar? their behavior is different.
        self.labels = {C.Entrypoint.name:Entrypoint, **labels}
        self.cached_funcs = []
        self.label_funcs = {}
        self.extent = 0
        def walk(spec):
            # validate spec
            if not isinstance(spec, (list, tuple)) or not isinstance(spec[0], T):
                raise ValueError(f'unexpected spec: {spec!r}')

            t = spec[0]
            method = getattr(self, t.name)
            args = tuple(s if isinstance(s, (str,int)) else walk(s) for s in spec[1:])

            @wraps(method)
            def call(idx):
                if (x:=method(idx, *args)):
                    idx, v = x
                    self.extent = max(self.extent, idx)
                return x

            # index may need to create new labels that aren't explicitly given
            if t == T.Index and args not in self.label_funcs:
                name, offset = args
                l, *a = self.labels[name]
                self.label_funcs[args] = walk((l, *a[offset:]))

            # disable caching for Label and Index
            # they just pass-through to another cached function
            if t not in (T.Label, T.Index):
                call = cache(call)
                self.cached_funcs.append(call)

            return call

        for label, s in self.labels.items():
            #print(label)
            if s and s[0] == T.Node:
                s = [T.Argument, s]
            self.label_funcs[label] = walk(s)
    def update(self, **labels):
        l = {}
        l.update(self.labels)
        l.update({k:squaredCircle(v) for k,v in labels.items()})
        self.__init__(**l)

    def parse(self, text):
        self.text = text
        for f in self.cached_funcs:
            f.cache_clear()
        self.extent = 0
        result = self.label_funcs[C.Entrypoint.name](0)
        if result is None:
            lines = text.split('\n')
            lineno = text.count('\n', 0, self.extent)
            if lineno > 0:
                print(f'{lineno-1:03}:{lines[lineno-1]}')
                pre = text.rfind('\n', 0, self.extent)
            else:
                pre = 0
            print(f'{lineno:03}:{lines[lineno]}')
            print('^'.rjust(self.extent-pre + 4, ' '))
            print(f'{lineno+1:03}:{lines[lineno+1]}')
            print(f'ParseError: failed after line={lineno} char={pre}')

            return None
        _, result = result
        # TODO
        #print(result)
        if result:
            memo = []
            self._trim(result, memo=memo)
            return memo[0]
        return None

    def fmt(self, tree) -> str:
        # TODO setup inverse parsing (fmt)
        # create a lens that lets you iterate over a trees arguments
        # paths : List[List[int]] with negative numbers indicating going up the tree
        # re-parse the original grammar and eval with new semantics


        # return None if the tree cannot match the spec
        def walk(spec, tree):
            match tree:
                case [T.Node, name, body]:
                    pass
                case [T.Argument, body]:
                    pass
                case list():
                    pass
                case str():
                    pass
                case x:
                    raise ValueError(f'unexpected value in tree: {x!r}')
            yield ''
        return ''.join(walk(self.labels, tree))
        

    def _trim(self, obj, keep=True, memo=None):
        # arguments under nodes or labels should 
        # reduce nesting to just Nodes
        # under the top level, return everything
        # need to filter out arguments, nodes
        # join sequential strings and flatten nested lists

        if memo is None:
            memo = []
        match obj:
            case [T.Node, name, body]:
                if not keep:
                    return
                memo = [name]
                #print(f'before node  {name}  body:{body!r} memo:{memo!r}')
                body = self._trim(body, False, memo)
                #print(f'after  node  {name}  body:{body!r} memo:{memo!r}')
                return memo
            case [T.Argument, body]:
                #print(f'before arg   {memo[0] if memo else ""!r} body:{body!r} memo:{memo!r}')
                body = self._trim(body, True, [])
                memo.append(body)
                #print(f'after  arg   {memo[0] if memo else ""!r} body:{body!r} memo:{memo!r}')
                return body
            case [T.Label, name, body]:
                if not keep:
                    return
                memo2 = []
                #print(f'before label {name} body:{body!r} memo2:{memo2!r}')
                body = self._trim(body, False, memo2)
                #print(f'after  label {name} body:{body!r} memo2:{memo2!r}')
                return body
            case list():
                #print(f'before list  body:{obj!r} memo:{memo!r}')
                body = []
                prev_str = False
                for a in obj:
                    x = self._trim(a, keep, memo)
                    cur_str = isinstance(x, str)
                    if prev_str and cur_str:
                        body[-1]+=x
                    else:
                        if x:
                            body.append(x)
                    prev_str = cur_str
                match len(body):
                    case 0:
                        body = None
                    case 1:
                        body = body[0]
                #print(f'after  list  body:{body!r}, memo:{memo!r}')
                return body
            case _:
                return obj

    # lexing functions return a tuple (idx, content) if it matches else None
    # idx is the index from which to continue
    # content may be
    #   None: filtered out
    #   str: literal text
    #   list:, or a Node
    #
    # this make extensive use of the fact that functions implicitly return None

    def Dot(self, idx):
        if idx < len(self.text):
            return idx + 1, self.text[idx]

    def String(self, idx, literal):
        # use idx as starting offset
        if self.text.startswith(literal, idx):
            return idx + len(literal), literal

    def CharClass(self, idx, *chars):
        # if we're already at the end of input then we can't match
        if idx >= len(self.text):
            return None
        #print(idx, self.text[idx], chars)
        for crange in chars:
            # each of these values will be a single character, which comparisons sort in lexographical order.
            #print(f'{crange[0]!r} <= {self.text[idx]!r} <= {crange[-1]!r}')
            if crange[0] <= self.text[idx] <= crange[-1]:
                #print('true!')
                return idx +1, self.text[idx]

    def Choice(self, idx, *exprs):
        for expr in exprs:
            if (x:=expr(idx)) is not None:
                return x

    def Sequence(self, idx, *exprs):
        c = []
        for expr in exprs:
            if (x:= expr(idx)) is None:
                return None
            idx, v = x
            c.append(v)
        return idx, c

    def OneOrMore(self, idx, expr):
        if (x:=expr(idx)) is None:
            return
        idx, *c = x
        while (x:=expr(idx)) is not None:
            idx, v = x
            c.append(v)
        return idx, c

    def ZeroOrMore(self, idx, expr):
        c = []
        while (x:=expr(idx)) is not None:
            idx, v = x
            c.append(v)
        return idx, c

    def ZeroOrOne(self, idx, expr):
        if (x:=expr(idx)) is None:
            return idx, None
        return x

    def Lookahead(self, idx, expr):
        if expr(idx) is not None:
            return idx, None

    def NotLookahead(self, idx, expr):
        if expr(idx) is None:
            return idx, None

    def Node(self, idx, name, expr):
        if (x:=expr(idx)):
            idx, v = x
            return idx, [T.Node, name, v]

    def Argument(self, idx, expr):
        if (x:=expr(idx)):
            idx, v = x
            return idx, [T.Argument, v]

    def Label(self, idx, name):
        #return self.label_funcs[name](idx)
        if (x:=self.label_funcs[name](idx)):
            idx,v = x
            return idx, [T.Label, name, v]

    def Index(self, idx, name, offset):
        return self.Label(idx, (name, offset))

def _fixedpoint():
    # names
    choice = T.Choice.name
    sequence = T.Sequence.name
    zeroorone = T.ZeroOrOne.name
    zeroormore = T.ZeroOrMore.name
    oneormore = T.OneOrMore.name
    lookahead = T.Lookahead.name
    notlookahead = T.NotLookahead.name
    label = T.Label.name
    string = T.String.name
    index = T.Index.name
    node = T.Node.name
    argument = T.Argument.name
    definition = C.Definition.name
    dot = T.Dot.name
    parseexpr = 'ParseExpr'
    primary = 'Primary'
    spacing = 'Spacing'
    comment = 'Comment'
    leftarrow = 'LEFTARROW'
    slash = 'SLASH'
    arg = 'ARG'
    amp = 'AMP'
    bang = 'BANG'
    question = 'QUESTION'
    star = 'STAR'
    plus = 'PLUS'
    OPEN = 'OPEN'
    close = 'CLOSE'
    space = 'SPACE'
    eol = 'EOL'
    eof = 'EOF'
    char = 'Char'

    # labels
    lspacing = [T.Label, spacing]
    lcomment = [T.Label, comment]
    lleftarrow = [T.Label, leftarrow]
    lslash = [T.Label, slash]
    larg = [T.Label, arg]
    lamp = [T.Label, amp]
    lbang = [T.Label, bang]
    lquestion = [T.Label, question]
    lstar = [T.Label, star]
    lplus = [T.Label, plus]
    lopen = [T.Label, OPEN]
    lclose = [T.Label, close]
    lspace = [T.Label, space]
    leol = [T.Label, eol]
    leof = [T.Label, eof]
    llabel = [T.Label, label]
    lchar = [T.Label, char]
    lnode = [T.Label, node]
    ldefinition = [T.Label, definition]
    
    # labels
    anotlookahead = [T.Argument, [T.Label, notlookahead]]
    adefinition = [T.Argument, [T.Label, definition]]
    aparseexpr  = [T.Argument, [T.Label, parseexpr]]
    asequence   = [T.Argument, [T.Label, sequence]]
    azeroorone  = [T.Argument, [T.Label, zeroorone]]
    azeroormore = [T.Argument, [T.Label, zeroormore]]
    aoneormore  = [T.Argument, [T.Label, oneormore]]
    alookahead  = [T.Argument, [T.Label, lookahead]]
    aargument   = [T.Argument, [T.Label, argument]]
    aprimary    = [T.Argument, [T.Label, primary]]
    achoice     = [T.Argument, [T.Label, choice]]
    adot    = [T.Argument, [T.Label, dot]]
    alabel  = [T.Argument, [T.Label, label]]
    astring = [T.Argument, [T.Label, string]]
    aindex  = [T.Argument, [T.Label, index]]
    achar = [T.Argument, [T.Label, char]]
    anode  = [T.Argument, [T.Label, node]]
    
    az = 'a-z'
    AZ = 'A-Z'
    d  = '0-9'
    d2 = [T.CharClass, '0-2']
    d7 = [T.CharClass, '0-7']
    d9 = [T.CharClass, d]
    crange = [T.Choice, [T.Argument, [T.Sequence, lchar, [T.String, '-'], lchar]], achar]
    
    q = [T.String, "'"]
    Q = [T.String, '"']
    b = [T.String, '[']
    bb = [T.String, ']']
    apex = lambda i:[T.Argument, [T.Index, parseexpr, i]]
    bs = [T.String, '\\']
    
    labels = {
        C.Entrypoint.name:[T.Node, C.Entrypoint.name, [T.Sequence, lspacing, [T.Argument, [T.OneOrMore, ldefinition]], leof]],
        definition:[T.Node, definition,
            [T.Sequence, [T.Argument, [T.Choice, llabel, lnode]], lleftarrow, aparseexpr]],
        parseexpr: [T.Choice, achoice, asequence, [T.Choice, alookahead, anotlookahead, aargument], [T.Choice, azeroorone, azeroormore, aoneormore],  aprimary],
    
        T.Choice.name: [T.Node, T.Choice.name,
            [T.Sequence, apex(1), [T.OneOrMore, [T.Sequence, lslash, apex(1)]]]],
        T.Sequence.name: [T.Node, T.Sequence.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 2]], [T.OneOrMore, [T.Argument, [T.Index, parseexpr, 2]]]]],

        T.Lookahead.name: [T.Node, T.Lookahead.name,
            [T.Sequence, lamp, [T.Argument, [T.Index, parseexpr, 3]]]],
        T.NotLookahead.name: [T.Node, T.NotLookahead.name,
            [T.Sequence, lbang, [T.Argument, [T.Index, parseexpr, 3]]]],
        T.Argument.name: [T.Node, T.Argument.name,
            [T.Sequence, larg, [T.Argument, [T.Index, parseexpr, 3]]]],

        T.ZeroOrOne.name: [T.Node, T.ZeroOrOne.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 4]], lquestion]],
        T.ZeroOrMore.name: [T.Node, T.ZeroOrMore.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 4]], lstar]],
        T.OneOrMore.name: [T.Node, T.OneOrMore.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 4]], lplus]],

        primary:[T.Choice,
                 [T.Sequence, lopen, aparseexpr, lclose],
                 aindex,
                 [T.Sequence, alabel, [T.NotLookahead, lleftarrow]],
                 astring, [T.Argument, [T.Label, T.CharClass.name]], adot],
        T.Node.name: [T.Node, T.Node.name,
            [T.Sequence, larg, alabel]],
        T.Index.name: [T.Node, T.Index.name,
                       [T.Sequence, alabel, [T.String, ':'], [T.Argument, [T.OneOrMore, d9]], lspacing]],
        T.Label.name: [T.Node, T.Label.name,
                       [T.Sequence, [T.Argument, [T.Sequence, [T.CharClass, az, AZ, '_'], [T.ZeroOrMore, [T.CharClass, az, AZ, '_', d]]]], lspacing]],

        spacing: [T.ZeroOrMore, [T.Choice, lspace, lcomment]],
        comment: [T.Sequence, [T.String, '#'], [T.ZeroOrMore, [T.Sequence, [T.NotLookahead, leol], [T.Dot]]], [T.Choice, leol, leof]],
        leftarrow: [T.Sequence, [T.String, '<-'], lspacing],
        slash: [T.Sequence, [T.String, '/'], lspacing],
        arg: [T.Sequence, [T.String, '%'], lspacing],
        amp: [T.Sequence, [T.String, '&'], lspacing],
        bang: [T.Sequence, [T.String, '!'], lspacing],
        question: [T.Sequence, [T.String, '?'], lspacing],
        star: [T.Sequence, [T.String, '*'], lspacing],
        plus: [T.Sequence, [T.String, '+'], lspacing],
        OPEN: [T.Sequence, [T.Argument, [T.String, '(']], lspacing],
        close: [T.Sequence, [T.String, ')'], lspacing],
        dot: [T.Node, T.Dot.name, [T.Sequence, [T.String, '.'], lspacing]],
        space: [T.Choice, [T.String, ' '], [T.String, '\t'], leol],
        eol: [T.Choice, [T.String, '\r\n'], [T.String, '\r'], [T.String, '\n']],
        eof: [T.NotLookahead, [T.Dot]],
        T.CharClass.name: [T.Node, T.CharClass.name, [T.Sequence, b, 
                         crange, [T.ZeroOrMore, [T.Sequence, [T.NotLookahead, bb], crange]],
                         bb, lspacing]],
        T.String.name: [T.Node, T.String.name,
                        [T.Sequence, [T.Choice,
                            [T.Sequence, Q, [T.Argument, [T.ZeroOrMore, [T.Sequence, [T.NotLookahead,  Q], lchar]]], Q],
                            [T.Sequence, q, [T.Argument, [T.ZeroOrMore, [T.Sequence, [T.NotLookahead,  q], lchar]]], q],
                        ], lspacing]],
        char: [T.Argument, [T.Choice,
               [T.Sequence, bs, [T.CharClass, *"][nrt'\"\\"]],
               [T.Sequence, bs, d2, d7, d7],
               [T.Sequence, bs, d7,[T.ZeroOrOne, d7]],
               [T.Sequence, [T.NotLookahead, bs], [T.Dot]] ]],
    }
    return BuildParser(**labels), labels

fixedpoint, labels = _fixedpoint()

escape_map = {'\n':'\\n', '\t':'\\t', '\r':'\\r', '\\':'\\\\'}
def escape(string, cmap=escape_map, undo=False):
    if undo:
        for k,v in cmap.items():
            string = string.replace(v, k)
    else:
        for k,v in cmap.items():
            string = string.replace(k, v)
    return string
def unescape(string, cmap=escape_map):
    return escape(string, cmap, undo=True)

# TODO this is really an evaluator and should be in a separate file
def squaredCircle(tree):
    """convert an AST into labels suitable to build a parser."""
    match tree:
        case [C.Entrypoint.name, [C.Definition.name, *args]]:
            pass
            exprs = [[C.Definition.name, *args]]
        case [C.Entrypoint.name, exprs]:
            pass
        case _:
            exprs = [tree]
    labels = {}
    def walk(b):
        match b:
            case [T.Index.name, [T.Label.name, name], idx]:
                return [T.Index, name, int(idx)]
            case [T.String.name, s]:
                return [T.String, unescape(s)]
            case [T.CharClass.name, *args]:
                return [T.CharClass, *map(unescape, args)]
            case [t, *b]:
                return [T[t], *(walk(x) for x in b)]
            case _:
                return b
    for expr in exprs:
        match expr:
            case [C.Definition.name, [T.Label.name, lname], body]:
                #print(f'processing label {lname}')
                labels[lname] = walk(body)
            case [C.Definition.name, [T.Node.name, [T.Label.name, nname]], body]:
                #print(f'processing node  {nname}')
                labels[nname] = walk([T.Node.name, nname, body])
            case _:
                print(f'not processing {expr!r}')
                pass
    return labels


