import enum
from functools import cache, wraps
from collections import UserList

class namedlist(UserList):
    def __init__(self, arg=(), name=None):
        super().__init__(arg)
        self.name = name
        
    def __str__(self):
        if self.name:
            return self.name + super().__str__()
        return super().__str__()
    def __repr__(self):
        if self.name:
            return self.name + super().__repr__()
        return super().__repr__()


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
        def walk(spec):
            # validate spec
            if not isinstance(spec, (list, tuple)) or not isinstance(spec[0], T):
                raise ValueError(f'unexpected spec: {spec!r}')

            t = spec[0]
            method = getattr(self, t.name)
            args = tuple(s if isinstance(s, (str,int)) else walk(s) for s in spec[1:])

            @wraps(method)
            def call(idx):
                return method(idx, *args)

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

    def parse(self, text):
        self.text = text
        for f in self.cached_funcs:
            f.cache_clear()
        result = self.label_funcs[C.Entrypoint.name](0)
        # TODO
        return result
        #print(result[1])
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
        

    def _trim(self, obj, keep=True, memo=None):
        # arguments under nodes or labels should 
        # reduce nesting to just Nodes
        # under the top level, return everything
        # need to filter out arguments, nodes
        # join sequential strings and flatten nested lists

        # a node should reach down to just its arguments
        # a label s
        #def node(n, memo):
        #    match n:
        #        case [T.Node, *_]:
        #            return memo
        #        case [T.Label, *_]:
        #            pass
        #        case [T.Argument, body]: memo.append(argument(body))
        #        case list():
        #            for x in n:
        #                node(x, memo)
        #def argument(n):
        #    match n:
        #        case [T.Node, *args]:
        #            return node(n, [])
        #        case [T.Label, body]:
        #            return label(body)
        #        case [T.Argument, body]:
        #            return argument(body)

        #    if not isinstance(n, list):
        #        return memo
        #    # search for arguments

        #    return memo

        #print(f'_trim({obj[0] if obj else obj}, {keep}, {id(memo)}')
        match obj:
            case [T.Node, name, body]:
                if not keep:
                    return
                #memo = namedlist([name], name='node')
                memo = [name]
                self._trim(body, False, memo)
                return memo
            case [T.Argument, body]:
                body = self._trim(body, True, memo)
                if memo is not None and memo is not body:
                    memo.append(body)
                return body
            case [T.Label, name, body]:
                if not keep:
                    return
                #memo2 = namedlist(name='label') if memo else memo
                memo2 = [] if memo else memo
                body = self._trim(body, keep, memo2)
                return memo2
            case list():
                #out = namedlist(name='list')
                out = []
                prev_str = False
                for a in obj:
                    x = self._trim(a, keep, memo)
                    cur_str = isinstance(x, str)
                    if prev_str and cur_str:
                        out[-1]+=x
                    else:
                        if x:
                            out.append(x)
                    prev_str = cur_str
                if len(out) == 1:
                    return out[0]
                if not out:
                    return None
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
            return idx, [T.Label, name, v]

    def Index(self, idx, name, offset):
        return self.Label(idx, (name, offset))
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
    achar = [T.Argument, [T.Label, char]]
    anode  = [T.Argument, [T.Label, node]]
    
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
            [T.Sequence, [T.Choice, alabel, anode], lleftarrow, aparseexpr]],
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
            [T.Sequence, larg, alabel]],
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
        eol: [T.String, '\r\n', '\r', '\n'],
        eof: [T.NotLookahead, [T.Dot]],
        T.Label.name: [T.Node, T.Label.name,
                       [T.Sequence, [T.Argument, [T.Sequence, [T.String, *az, *AZ, '_'], [T.ZeroOrMore, [T.String, *az, *AZ, '_', *d]]]], lspacing]],
        T.String.name: [T.Node, T.String.name,
                        [T.Sequence, [T.Choice,
                            [T.Sequence, qq, [T.Argument, [T.ZeroOrMore, [T.Sequence, [T.NotLookahead, qq], achar]]], qq],
                            [T.Sequence, q, [T.Argument, [T.ZeroOrMore, [T.Sequence, [T.NotLookahead, q], achar]]], q],
                            [T.Sequence, b, [T.OneOrMore, [T.Argument, [T.Sequence, [T.NotLookahead, bb], achar]]], bb]
                        ], lspacing]],
        char: [T.Argument, [T.Choice,
               [T.Sequence, [T.String, '\\'], [T.String, *"nrt'[]\"\\"]],
               [T.Sequence, [T.String, '\\'], d2, d7, d7],
               [T.Sequence, [T.String, '\\'], d7,[T.ZeroOrOne, d7]],
               [T.Sequence, [T.NotLookahead, [T.String, '\\']], [T.Dot]] ]],
    }
    return BuildParser(**labels), labels

fixedpoint, labels = _fixedpoint()

# TODO this is really an evaluator and should be in a separate file
def squaredCircle(tree):
    match tree:
        case [C.Entrypoint.name, *exprs]:
            pass
        case _:
            raise ValueError
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


