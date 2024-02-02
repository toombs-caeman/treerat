import enum
from functools import cache, wraps

#__all__ = ['BuildParser', 'T']

"""
'specs' are a function serialized into a lisp-like syntax
each function is a list with the first element being T that indicates the function, and following by string and spec arguments to that function

This allows a spec to be valid json.
"""
# the types recognized in spec
T = enum.Enum('T', (
    'Dot',
    'String',

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

# control names
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
        self.spec = Entrypoint
        self.labels = labels
        self.cached_funcs = []
        self.label_funcs = {}
        def walk(spec):
            # validate spec
            if not isinstance(spec, (list, tuple)) or not isinstance(spec[0], T):
                raise ValueError(f'unexpected spec: {spec!r}')

            t = spec[0]
            method = getattr(self, t.name)
            args = tuple(s if isinstance(s, (str,int)) else walk(s) for s in spec[1:])

            @wraps(method)
            def call(idx):
                try:
                    return method(idx, *args)
                except TypeError:
                    raise ValueError(method.__name__, args)

            # index may need to create new labels that aren't explicitly given
            if t == T.Index and args not in self.label_funcs:
                name, offset = args
                l, *a = labels[name]
                self.label_funcs[args] = walk((l, *a[offset:]))

            # disable caching for Label and Index
            # they just pass-through to another cached function
            if t not in (T.Label, T.Index):
                call = cache(call)
                self.cached_funcs.append(call)

            return call

        for label, s in labels.items():
            #print(label)
            self.label_funcs[label] = walk(s)
        # the toplevel spec forms the entrypoint
        self.entrypoint = walk(Entrypoint)



    def parse(self, text):
        self.text = text
        for f in self.cached_funcs:
            f.cache_clear()
        result = self.entrypoint(0)
        if result:
            return self._trim(result[1])
        return None

    def fmt(self, tree) -> str:
        # TODO setup inverse parsing (fmt)
        # create a lens that lets you iterate over a trees arguments
        # paths : List[List[int]] with negative numbers indicating going up the tree

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
        return ''.join(walk(self.spec, tree))
        

    def _trim(self, obj, memo=None):
        #return obj
        # reduce nesting to just Nodes
        # under the top level, return everything
        # need to filter out arguments, nodes
        # join sequential strings and flatten nested lists
        match obj:
            case [T.Node, name, body]:
                memo = [name]
                self._trim(body, memo)
                return memo
            case [T.Argument, body]:
                # TODO is None right here? or is it better to also include labels until this step
                body = self._trim(body, memo)
                if memo:
                    memo.append(body)
                return body
            case [T.Label, body]:
                memo2 = []
                body = self._trim(body, memo2)
                if memo:
                    memo.extend(memo2)
                return body
            case list():
                out = []
                for a in obj:
                    x = self._trim(a, memo)
                    if isinstance(x, str) and out and isinstance(out[-1], str):
                        out[-1]+=x
                    else:
                        if x is not None:
                            out.append(x)
                if len(out) == 1:
                    return out[0]
                return out
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
    # and that None is falsy while any match will be truthy

    def Dot(self, idx):
        if idx < len(self.text):
            return idx + 1, self.text[idx]

    def String(self, idx, *literals):
        for literal in literals:
            if self.text.startswith(literal, idx):
                return idx + len(literal), literal

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
        if (x:=self.label_funcs[name](idx)):
            idx,v = x
            return idx, [T.Label, v]

    def Index(self, idx, name, offset):
        if (x:=self.label_funcs[name, offset](idx)):
            idx,v = x
            return idx, [T.Label, v]

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
    main = C.Entrypoint.name
    parserun = 'ParseRun'
    expr = 'Expr'
    ffdefinition = 'FFDefinition'
    definition = C.Definition.name
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
    dot = 'DOT'
    space = 'SPACE'
    eol = 'EOL'
    eof = 'EOF'
    CLASS = 'Class'
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
    
    az = 'abcdefghijklmnopqrstuvwxyz'
    AZ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    d  = '9876543210'
    d2 = [T.String, *d[6:]]
    d7 = [T.String, *d[2:]]
    d9 = [T.String, *d]
    
    q = [T.String, "'"]
    qq = [T.String, '"']
    b = [T.String, '[']
    bb = [T.String, ']']
    apex = lambda i:[T.Argument, [T.Index, parseexpr, i]]
    
    labels = {
        C.Entrypoint.name:[T.Node, C.Entrypoint.name, [T.Sequence, lspacing, [T.OneOrMore, adefinition], leof]],
        definition:[T.Node, definition,
            [T.Sequence, [T.Argument, [T.Choice, llabel, lnode]], lleftarrow, aparseexpr]],
        parseexpr: [T.Choice, achoice, asequence, [T.Choice, azeroorone, azeroormore, aoneormore], [T.Choice, alookahead, anotlookahead, aargument], aprimary],
    
        T.Choice.name: [T.Node, T.Choice.name,
            [T.Sequence, apex(1), [T.OneOrMore, [T.Sequence, lslash, apex(1)]]]],
        T.Sequence.name: [T.Node, T.Sequence.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 2]], [T.OneOrMore, [T.Argument, [T.Index, parseexpr, 2]]]]],
        T.ZeroOrOne.name: [T.Node, T.ZeroOrOne.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 3]], lquestion]],
        T.ZeroOrMore.name: [T.Node, T.ZeroOrMore.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 3]], lstar]],
        T.OneOrMore.name: [T.Node, T.OneOrMore.name,
            [T.Sequence, [T.Argument, [T.Index, parseexpr, 3]], lplus]],
        T.Lookahead.name: [T.Node, T.Lookahead.name,
            [T.Sequence, lamp, [T.Argument, [T.Index, parseexpr, 4]]]],
        T.NotLookahead.name: [T.Node, T.NotLookahead.name,
            [T.Sequence, lbang, [T.Argument, [T.Index, parseexpr, 4]]]],
        T.Argument.name: [T.Node, T.Argument.name,
            [T.Sequence, larg, [T.Argument, [T.Index, parseexpr, 4]]]],
        T.Node.name: [T.Node, T.Node.name,
            [T.Sequence, larg, [T.Argument, llabel]]],
        primary:[T.Choice,
                 [T.Sequence, lopen, aparseexpr, lclose],
                 aindex,
                 [T.Sequence, alabel, [T.NotLookahead, lleftarrow]],
                 astring, adot],
        T.Index.name: [T.Node, T.Index.name,
                       [T.Sequence, alabel, [T.String, ':'], [T.Argument, [T.OneOrMore, d9]], lspacing]],
        spacing: [T.ZeroOrMore, [T.Choice, lspace, lcomment]],
        comment: [T.Sequence, [T.String, '#'], [T.ZeroOrMore, [T.Sequence, [T.NotLookahead, leol], [T.Dot]]], leol],
        leftarrow: [T.Sequence, [T.String, '<-'], lspacing],
        slash: [T.Sequence, [T.String, '/'], lspacing],
        arg: [T.Sequence, [T.String, '%'], lspacing],
        amp: [T.Sequence, [T.String, '&'], lspacing],
        bang: [T.Sequence, [T.String, '!'], lspacing],
        question: [T.Sequence, [T.String, '?'], lspacing],
        star: [T.Sequence, [T.String, '*'], lspacing],
        plus: [T.Sequence, [T.String, '+'], lspacing],
        OPEN: [T.Sequence, [T.String, '('], lspacing],
        close: [T.Sequence, [T.String, ')'], lspacing],
        dot: [T.Sequence, [T.String, '.'], lspacing],
        space: [T.Choice, [T.String, ' '], [T.String, '\t'], leol],
        #eol: [T.Choice, [T.String, '\\r\\n'], [T.String, '\\r'], [T.String, '\\n']],
        eol: [T.String, '\r\n', '\r', '\n'],
        eof: [T.NotLookahead, [T.Dot]],
        T.Label.name: [T.Node, T.Label.name,
                       [T.Sequence, [T.Argument, [T.Sequence, [T.String, *az, *AZ, '_'], [T.ZeroOrMore, [T.String, *az, *AZ, '_', *d]]]], lspacing]],
        T.String.name: [T.Node, T.String.name,
                        [T.Sequence, [T.Choice,
                            [T.Sequence, qq, [T.Argument, [T.ZeroOrMore, [T.Sequence, [T.NotLookahead, qq], lchar]]], qq],
                            [T.Sequence, q, [T.Argument, [T.ZeroOrMore, [T.Sequence, [T.NotLookahead, q], lchar]]], q],
                            [T.Sequence, b, [T.OneOrMore, [T.Argument, [T.Sequence, [T.NotLookahead, bb], lchar]]], bb]
                        ], lspacing]],
        char: [T.Choice,
               [T.Sequence, [T.String, '\\'], [T.String, *"nrt'[]\"\\"]],
               [T.Sequence, [T.String, '\\'], d2, d7, d7],
               [T.Sequence, [T.String, '\\'], d7,[T.ZeroOrOne, d7]],
               [T.Sequence, [T.NotLookahead, [T.String, '\\']], [T.Dot]] ],
    }
    # TODO wrap parser to convert strings to T
    return BuildParser(**labels), labels

fixedpoint, labels = _fixedpoint()

def squaredCircle(tree):
    match tree:
        case [C.Entrypoint.name, *exprs]:
            pass
        case _:
            raise ValueError
    #names = tuple(t.name for t in T)
    labels = {}
    def walk(b):
        match b:
            case [t, *b]:
                return [T[t], *(walk(x) for x in b)]
            case _:
                return b
    for expr in exprs:
        match expr:
            case [C.Definition.name, [T.Label.name, lname], body]:
                labels[lname] = walk(body)
            case [C.Definition.name, [T.Node.name, [T.Label.name, nname]], body]:
                labels[nname] = walk([T.Node.name, nname, body])
            case _:
                pass
    return labels


