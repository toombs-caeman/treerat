from functools import cache, wraps

# TODO error recovery marker in fixedpoint?
__all__ = ['node', 'Parser', 'ParseError']

class ParseError(Exception):
    """raised if parser fails on input while in strict mode"""

class T:
    """To mitigate typos, define all the strings used internally as identifiers"""

    # input node kinds
    choice = 'Choice'
    zeroorone = 'ZeroOrOne'
    zeroormore = 'ZeroOrMore'
    oneormore = 'OneOrMore'
    lookahead = 'Lookahead'
    notlookahead = 'NotLookahead'
    index = 'Index'
    definition = 'Definition'
    dot = 'Dot'

    # input/internal node kinds
    sequence = 'Sequence'
    label = 'Label'
    string = 'String'
    node = 'Node'
    argument = 'Argument'

    # non-terminal symbols in the fixedpoint grammar definition
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
    charclass = 'CharClass'
    # default start symbol
    start = 'start'
class node:
    """generic tree node with some metadata"""
    __slots__ = ['kind', 'start', 'stop', 'children']
    def __init__(self, kind, *children, start:int=..., stop:int=...):
        self.kind = kind
        self.start = start
        self.stop = stop
        self.children = children
    def __iter__(self):
        return iter(self.children)
    def __getitem__(self, __key):
        return self.children[__key]
    def __hash__(self):
        return hash((self.kind, self.children))
    def __eq__(self, __o):
        return isinstance(__o, node) and self.kind == __o.kind and self.children == __o.children
    def __repr__(self):
        return f'{type(self).__name__}{(self.kind, *self.children)!r}'


class Parser:
    """
    A generic packrat parser.

    The parser can be initialized with a language specification,
    given as an abstract syntax tree containing Definition statements,
    a dictionary of symbols to the corresponding syntax tree, or a string.
    If no specification is given, the "fixedpoint" grammar is used.

    If a language specification is given as a string, it will be parsed according to the fixedpoint grammar
    and the resuting syntax tree will be used to initialize the parser as normal.

    The fixedpoint is named as such because parsing the fixedpoint grammar with a fixedpoint parser
    produces a syntax tree which can directly initialize an identical parser.

    The fixedpoint language itself is a small extension of the Parsing Expression Grammar (PEG), which adds the '%' and ':' operator.
    '%' allows the language to specify which symbols to retain in the output, and which should generate nodes in the resulting abstract syntax tree.
    ':' allows more convenient construction of operator precedence but is only syntactic sugar, strictly speaking.

    For example take the following grammar, which recognizes one or more math expressions separated with semicolons:
    %start <- %Expr (';' %Expr )* ';'? !.
    Expr   <- (%Add / %Sub) / (%Mul / %Div) / %Float / %Int / '(' %Expr ')'
    %Add   <- %Expr:1 PLUS %Expr
    %Sub   <- %Expr:1 MINUS %Expr
    %Mul   <- %Expr:2 (STAR %Expr:1)+
    %Div   <- %Expr:2 (SLASH %Expr:1)+
    %Float <- %(NUM '.' NUM) SPACE
    %Int   <- %NUM SPACE
    NUM    <- %[0-9]+
    OPEN   <- '(' SPACE
    CLOSE  <- ')' SPACE
    PLUS   <- '+' SPACE
    MINUS  <- '-' SPACE
    STAR   <- '*' SPACE
    SLASH  <- '/' SPACE
    SPACE  <- ' '*

    On the left hand side of a definition, '%' denotes that the symbol generates a node in the output.
    Non-terminal symbol definitions which lack a '%' are used only as labels for use in other definitions,
    and do not represent nodes in the output.
    As we can see, the output of parsing this grammar may contain nodes of kind start, Add, Sub, Mul, Div, Float, and Int.

    On the right hand side '%' designates that a symbol should be retained as an argument in the output.
    In the definition of Add, there are two arguments marked with '%' which must always match to successfully match Add,
    so the output node Add will always have two children. PLUS must also match in the process of matching Add,
    but the contents of PLUS are always discarded because it was not marked with '%' (its contents are empty anyway).
    In the definition of Div, the second argument may be repeated one or more times because the '+' operator encloses '%',
    therefore Div nodes have two or more children.
    Expr only ever has one arguement because, while '%' is used a few times, only one '%' expression will match at a time.
    Because Expr does not designate a node, the matched argument will be substituted directly in definitions where Expr
    is referenced, rather than encapsulating the argument itself.

    ':' refers to an implicit symbol based on an explicit definition. 'Expr:1' means to take every term of Expr except the first.
    In this case it is equivalent to the following definition:
    Expr:1 <- (%Mul / %Div) / %Float / %Int / '(' %Expr ')'
    The purpose of ':' is to make operator precedence easier to express.
    Some choices in Expr are grouped, even though an ungrouped choice is locally equivalent, to express that those
    operators have equal precedence.


    see also:
        https://en.wikipedia.org/wiki/Parsing_expression_grammar
        https://bford.info/pub/lang/peg.pdf

    TODO:
        detect mutual left recursion in a grammar and refuse to initialize
        provide partial parsings and extended error reporting
    """
    def __init__(self, __from=None, /, **labels:node):
        # rectify the incoming specification for internal use
        if __from is None and not labels:
            labels = fixedpoint.copy()
        else:
            match __from:
                case str():
                    __from = ast2labels(Parser()(__from))
                case dict():
                    __from = __from
                case node():
                    __from = ast2labels(__from)
                case _:
                    __from = {}
            __from.update(labels)
            labels = __from

        # resolve labels into cache-friendly function applications
        self.__cache_clears = []
        index = {}

        @cache
        def resolve(kind, *args):
            if kind == T.index:
                # create new label based on index into existing label
                name = args[0].name
                offset = args[1]
                newname = f'{name}:{offset}'
                index[newname] = node(labels[name].kind, *labels[name][int(offset):])
                # turn index into plain label
                kind = T.label
                args = (newname,)
            method = getattr(self, kind)

            @cache
            @wraps(method)
            def call(idx:int) -> node|None:
                if (n:=method(idx, *args)):
                    self.__extent = max(self.__extent, n.stop)
                return n

            self.__cache_clears.append(call.cache_clear)
            if kind == T.label:
                # make sure this is accessible later if there's an index into this label
                call.name = args[0]
            return call

        
        # walk the tree bottom up, applying term() to terminal values and func() to flattened nodes (non-terminals)
        def walk(n:node, func, term=lambda x:x):
            return func(n.kind, *(walk(c, func, term) if isinstance(c, node) else term(c) for c in n.children))
        self.labels = {name:walk(n, resolve) for name, n in labels.items()}
        # apply the new labels generated by indices in previous walk of resolve()
        # all indices will be resolved in a single pass
        self.labels.update({name:walk(n, resolve) for name,n in index.items()})

        self.__extent = 0
        self.__text = ''
        self.error = None

    def __call__(self, text:str, start='start', *, trim=True, strict=False) -> node|None:
        """
        Attempt to parse text as the given start symbol.

        Parsing always starts at the beginning of the text and tries to match the given start symbol.
        If parsing fails Parser.error is set, then ParseError is raised if strict otherwise None is returned.
        The parsed tree does not necessarily span the whole input text unless that is specified by the grammar.

        If trim is False, return the internal parse tree, rather than the output tree.
        The usual output can be obtained by passing the tree to Parser._trim()
        This is probably only useful for testing the parser.
        """
        # reset
        self.__text = text
        self.error = None
        self.cache_clear()

        # do parsing of self.__text from beginning with the start symbol
        ast = self.labels[start](0)

        if ast is None:
            lines = text.split('\n')
            lineno = text.count('\n', 0, self.__extent)
            self.error = []
            if lineno > 0:
                self.error.append(f'{lineno-1:03}:{lines[lineno-1]}')
                pre = text.rfind('\n', 0, self.__extent)
            else:
                pre = 0
            self.error.append(f'{lineno:03}:{lines[lineno]}')
            self.error.append('^'.rjust(self.__extent-pre + 4, ' '))
            if lineno + 1 < len(lines):
                self.error.append(f'{lineno+1:03}:{lines[lineno+1]}')
            self.error.append(f'ParseError: failed after line={lineno} char={pre}')
            if strict:
                raise ParseError('\n'.join(self.error))
        else:
            if trim:
                return self._trim(ast)
        return ast

    def cache_clear(self):
        for clear in self.__cache_clears:
            clear()

    def _trim(self, ast:node) -> node:
        """
        Convert internal parser representation into the output syntax tree.

        The untrimmed generated ast contains 5 kinds (Node, Argument, Label, Sequence, String) which are specific to the parser.

        Argument specifies that a subtree should be retained in the output as an argument the enclosing Node or Label.

        Node specifies a node in the output syntax tree.
        The first child is a string that specifies the output node's kind.

        Label indicates that this subtree was generated by a non-terminal symbol that does not represent a Node.
        Arguments of Labels are retained by the enclosing Node only if the Label is also marked with an Argument.

        Sequence represents a sequence of nodes. In general these are flattened in the output.

        The kinds of the trimmed ast are in the set {n[0] for n in walk(ast) if n.kind = 'Node'}
        The arguments of each output node are a flat list of the 

        """
        match ast.kind:
            case T.node:
                return self.__node(ast)
            case T.argument:
                return self._trim(ast[0])
            case T.string:
                return self.__unescape(ast[0])
            case T.label:
                return self.__label(ast)
            case T.sequence:
                args = map(self._trim, ast)
                # flatten sequence
                args = tuple(v for a in args for v in (a if isinstance(a, tuple) else (a,)))
                # check if empty
                if not args:
                    return ()
                # merge strings
                if all(isinstance(a, str) for a in args):
                    return self.__unescape(''.join(args))
                return args
            case _:
                raise ValueError

    def __node(self, ast:node, memo=None):
        if memo is None:
            memo = []
            newkind, body = ast
            self.__node(body, memo)
            return node(newkind, *memo, start=ast.start, stop=ast.stop)
        match ast.kind:
            case T.argument:
                memo.append(self._trim(ast))
            case T.sequence:
                for a in ast:
                    self.__node(a, memo)

    def __label(self, ast:node, memo=None):
        if memo is None:
            memo = []
            self.__label(ast[1], memo)
            match len(memo):
                case 0:
                    return self._trim(ast[1])
                case 1:
                    return memo[0]
                case _:
                    return tuple(memo)

        match ast.kind:
            case T.argument:
                memo.append(self._trim(ast))
            case T.sequence:
                for a in ast:
                    self.__node(a, memo)

    def __unescape(self, s, __map={'\\n':'\n', '\\t':'\t', '\\r':'\r', '\\\\':'\\'}):
        for k,v in __map.items():
            s = s.replace(k,v)
        return s

    def Dot(self, idx):
        if idx < len(self.__text):
            return node(T.string, self.__text[idx], start=idx, stop=idx+1)

    def String(self, idx, literal):
        if self.__text.startswith(literal, idx):
            return node(T.string, literal, start=idx, stop=idx+len(literal))

    def CharClass(self, idx, *chars):
        if idx >= len(self.__text):
            return
        for crange in chars:
            if crange[0] <= self.__text[idx] <= crange[-1]:
                return node(T.string, self.__text[idx], start=idx, stop=idx+1)

    def Choice(self, idx, *exprs) -> node|None:
        for expr in exprs:
            if (x:=expr(idx)) is not None:
                return x

    def Sequence(self, idx, *exprs):
        c = []
        for expr in exprs:
            if (x:= expr(idx)) is None:
                return None
            idx = x.stop
            c.append(x)
        return node(T.sequence, *c, start=c[0].start, stop=c[-1].stop)

    def OneOrMore(self, idx, expr):
        c = [expr(idx)]
        if c[0] is None:
            return
        while (x:=expr(c[-1].stop)) is not None:
            c.append(x)
        return node(T.sequence, *c, start=c[0].start, stop=c[-1].stop)

    def ZeroOrMore(self, idx, expr):
        c = []
        while (x:=expr(idx)) is not None:
            c.append(x)
            idx = x.stop
        if c:
            return node(T.sequence, *c, start=c[0].start, stop=c[-1].stop)
        return node(T.sequence, start=idx, stop=idx)

    def ZeroOrOne(self, idx, expr):
        if (x:=expr(idx)) is None:
            return node(T.sequence, start=idx, stop=idx)
        return x

    def Lookahead(self, idx, expr):
        if expr(idx) is not None:
            return node(T.sequence, start=idx, stop=idx)

    def NotLookahead(self, idx, expr):
        if expr(idx) is None:
            return node(T.sequence, start=idx, stop=idx)

    def Node(self, idx, name, expr):
        if (x:=expr(idx)):
            return node(T.node, name, x, start=x.start, stop=x.stop)

    def Argument(self, idx, expr):
        if (x:=expr(idx)):
            return node(T.argument, x, start=x.start, stop=x.stop)

    def Label(self, idx, name):
        if (x:=self.labels[name](idx)):
            return node(T.label, name, x, start=x.start, stop=x.stop)

    def Index(self, idx, name, offset):
        # this should be resolved into calls to self.Label during initialization
        raise NotImplementedError

def ast2labels(ast:node) -> dict[str, node]:
    """
    Used by parser internally to convert ast into labels.

    Technically an Evaluator since it is Callable[node]
    """
    new_labels = {}
    for n in ast[0]:
        if n.kind == T.definition:
            match n[0].kind:
                case T.node:
                    name = n[0][0][0]
                    new_labels[name] = node(T.node, name, n[1])
                case T.label:
                    name = n[0][0]
                    new_labels[name] = n[1]
                case _:
                    print(f'unrecognized node {n[0].kind!r} in definition')
        else:
            print(f'unrecognized statement {n[0].kind!r} in grammar')
    return new_labels

# the fixed point grammar, as a dictionary
fixedpoint = {
            'start': node('Node', 'start', node('Sequence', node('Label', 'Spacing'), node('Argument', node('OneOrMore', node('Label', 'Definition'))), node('Label', 'EOF'))),
            'Definition': node('Node', 'Definition', node('Sequence', node('Argument', node('Choice', node('Label', 'Label'), node('Label', 'Node'))), node('Label', 'LEFTARROW'), node('Argument', node('Label', 'ParseExpr')))),
            'ParseExpr': node('Choice', node('Argument', node('Label', 'Choice')), node('Argument', node('Label', 'Sequence')), node('Choice', node('Argument', node('Label', 'Lookahead')), node('Argument', node('Label', 'NotLookahead')), node('Argument', node('Label', 'Argument'))), node('Choice', node('Argument', node('Label', 'ZeroOrOne')), node('Argument', node('Label', 'ZeroOrMore')), node('Argument', node('Label', 'OneOrMore'))), node('Argument', node('Label', 'Primary'))),
            'Choice': node('Node', 'Choice', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '1')), node('OneOrMore', node('Sequence', node('Label', 'SLASH'), node('Argument', node('Index', node('Label', 'ParseExpr'), '1')))))),
            'Sequence': node('Node', 'Sequence', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '2')), node('OneOrMore', node('Argument', node('Index', node('Label', 'ParseExpr'), '2'))))),
            'Lookahead': node('Node', 'Lookahead', node('Sequence', node('Label', 'AMP'), node('Argument', node('Index', node('Label', 'ParseExpr'), '3')))),
            'NotLookahead': node('Node', 'NotLookahead', node('Sequence', node('Label', 'BANG'), node('Argument', node('Index', node('Label', 'ParseExpr'), '3')))),
            'Argument': node('Node', 'Argument', node('Sequence', node('Label', 'ARG'), node('Argument', node('Index', node('Label', 'ParseExpr'), '3')))),
            'ZeroOrOne': node('Node', 'ZeroOrOne', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '4')), node('Label', 'QUESTION'))),
            'ZeroOrMore': node('Node', 'ZeroOrMore', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '4')), node('Label', 'STAR'))),
            'OneOrMore': node('Node', 'OneOrMore', node('Sequence', node('Argument', node('Index', node('Label', 'ParseExpr'), '4')), node('Label', 'PLUS'))),
            'Primary': node('Choice', node('Sequence', node('Label', 'OPEN'), node('Argument', node('Label', 'ParseExpr')), node('Label', 'CLOSE')), node('Argument', node('Label', 'Index')), node('Sequence', node('Argument', node('Label', 'Label')), node('NotLookahead', node('Label', 'LEFTARROW'))), node('Argument', node('Label', 'String')), node('Argument', node('Label', 'CharClass')), node('Argument', node('Label', 'Dot'))),
            'Node': node('Node', 'Node', node('Sequence', node('Label', 'ARG'), node('Argument', node('Label', 'Label')))),
            'Index': node('Node', 'Index', node('Sequence', node('Argument', node('Label', 'Label')), node('String', ':'), node('Argument', node('OneOrMore', node('CharClass', '0-9'))), node('Label', 'Spacing'))),
            'Label': node('Node', 'Label', node('Sequence', node('Argument', node('Sequence', node('CharClass', 'a-z', 'A-Z', '_'), node('ZeroOrMore', node('CharClass', 'a-z', 'A-Z', '_', '0-9')))), node('Label', 'Spacing'))),
            'Spacing': node('ZeroOrMore', node('Choice', node('Label', 'SPACE'), node('Label', 'Comment'))),
            'Comment': node('Sequence', node('String', '#'), node('ZeroOrMore', node('Sequence', node('NotLookahead', node('Label', 'EOL')), node('Dot',))), node('Choice', node('Label', 'EOL'), node('Label', 'EOF'))),
            'LEFTARROW': node('Sequence', node('String', '<-'), node('Label', 'Spacing')),
            'SLASH': node('Sequence', node('String', '/'), node('Label', 'Spacing')),
            'ARG': node('Sequence', node('String', '%'), node('Label', 'Spacing')),
            'AMP': node('Sequence', node('String', '&'), node('Label', 'Spacing')),
            'BANG': node('Sequence', node('String', '!'), node('Label', 'Spacing')),
            'QUESTION': node('Sequence', node('String', '?'), node('Label', 'Spacing')),
            'STAR': node('Sequence', node('String', '*'), node('Label', 'Spacing')),
            'PLUS': node('Sequence', node('String', '+'), node('Label', 'Spacing')),
            'OPEN': node('Sequence', node('Argument', node('String', '(')), node('Label', 'Spacing')),
            'CLOSE': node('Sequence', node('String', ')'), node('Label', 'Spacing')),
            'Dot': node('Node', 'Dot', node('Sequence', node('String', '.'), node('Label', 'Spacing'))),
            'SPACE': node('Choice', node('String', ' '), node('String', '\t'), node('Label', 'EOL')),
            'EOL': node('Choice', node('String', '\r\n'), node('String', '\r'), node('String', '\n')),
            'EOF': node('NotLookahead', node('Dot',)),
            'CharClass': node('Node', 'CharClass', node('Sequence', node('String', '['), node('Choice', node('Argument', node('Sequence', node('Label', 'Char'), node('String', '-'), node('Label', 'Char'))), node('Argument', node('Label', 'Char'))), node('ZeroOrMore', node('Sequence', node('NotLookahead', node('String', ']')), node('Choice', node('Argument', node('Sequence', node('Label', 'Char'), node('String', '-'), node('Label', 'Char'))), node('Argument', node('Label', 'Char'))))), node('String', ']'), node('Label', 'Spacing'))),
            'String': node('Node', 'String', node('Sequence', node('Choice', node('Sequence', node('String', '"'), node('Argument', node('ZeroOrMore', node('Sequence', node('NotLookahead', node('String', '"')), node('Label', 'Char')))), node('String', '"')), node('Sequence', node('String', "'"), node('Argument', node('ZeroOrMore', node('Sequence', node('NotLookahead', node('String', "'")), node('Label', 'Char')))), node('String', "'"))), node('Label', 'Spacing'))),
            'Char': node('Argument', node('Choice', node('Sequence', node('String', '\\'), node('CharClass', ']', '[', 'n', 'r', 't', "'", '"', '\\')), node('Sequence', node('String', '\\'), node('CharClass', '0-2'), node('CharClass', '0-7'), node('CharClass', '0-7')), node('Sequence', node('String', '\\'), node('CharClass', '0-7'), node('ZeroOrOne', node('CharClass', '0-7'))), node('Sequence', node('NotLookahead', node('String', '\\')), node('Dot',))))}

