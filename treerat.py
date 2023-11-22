from pprint import pprint as pp
# parsing expession grammar (PEG)
# nice PEG visualization https://blog.bruce-hill.com/packrat-parsing-from-scratch
# the original paper, which describes PEGs as a PEG https://bford.info/pub/lang/peg.pdf

fp = '''
%Main <- Spacing %Expr+ (ParseRun / EOF)
%ParseRun <- 'parse_run' Spacing
Expr <- %(ParseDefinition / FFDefinition)
%FFDefinition <- '```python' Spacing %('def' Spacing %Label (!'`' Char)*) '```'
%ParseDefinition <- %(Label / Node) LEFTARROW %ParseExpr
ParseExpr  <- %Choice / %Sequence / (%ZeroOrOne / %ZeroOrMore / %OneOrMore) / (%Lookahead / %NotLookahead / %Argument) / %Primary
%Choice   <- %ParseExpr:1 (SLASH %ParseExpr:1)+
%Sequence <- %ParseExpr:2 (%ParseExpr:2)+
%ZeroOrOne  <- %ParseExpr:3 QUESTION
%ZeroOrMore <- %ParseExpr:3 STAR
%OneOrMore  <- %ParseExpr:3 PLUS
%Lookahead    <- AMP  %ParseExpr:4
%NotLookahead <- BANG %ParseExpr:4
%Argument     <- ARG  %ParseExpr:4
%Node         <- ARG %Label
Primary <- (OPEN %ParseExpr CLOSE) / (%Label !LEFTARROW) / %String / %Class / %DOT / %Index
%Index  <- %Label ':' %([0-9]+)
Spacing <- (Space / Comment)*
Comment <- '#' (!EOL .)* EOL
LEFTARROW  <- '<-' Spacing
SLASH     <- '/' Spacing
ARG       <- '%' Spacing
AMP       <- '&' Spacing
BANG      <- '!' Spacing
QUESTION  <- '?' Spacing
STAR      <- '*' Spacing
PLUS      <- '+' Spacing
OPEN      <- '(' Spacing
CLOSE     <- ')' Spacing
%DOT      <- '.' Spacing
Space <- ' ' / '\\t' / EOL
EOL <- '\\r\\n' / '\\r' / '\\n'
EOF <- !.
%Label <- %([a-zA-Z_] [a-zA-Z_0-9]*) Spacing
%String <- (('"' %(!'"' Char)* '"') / ("'" %(!"'" Char)* "'")) Spacing
%Class <- '[' %((!']' Char)+) ']' Spacing
Char <- %( ('\\'  [nrt'[\\]"\\\\]) / ('\\' [0-2] [0-7] [0-7]) / ('\\' [0-7] [0-7]?) / !'\\' .)
'''

main = 'Main'
parserun = 'ParseRun'
expr = 'Expr'
ffdefinition = 'FFDefinition'
definition = 'ParseDefinition'
parseexpr = 'ParseExpr'
choice = 'Choice'
sequence = 'Sequence'
zeroorone = 'ZeroOrOne'
zeroormore = 'ZeroOrMore'
oneormore = 'OneOrMore'
lookahead = 'Lookahead'
notlookahead = 'NotLookahead'
argument = 'Argument'
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
label = 'Label'
string = 'String'
CLASS = 'Class'
char = 'Char'
index = 'Index'
node = 'Node'

lmain = [label, main]
lparserun = [label, parserun]
lexpr = [label, expr]
lffdefinition = [label, ffdefinition]
ldefinition = [label, definition]
lparseexpr = [label, parseexpr]
lchoice = [label, choice]
lsequence = [label, sequence]
lzeroorone = [label, zeroorone]
lzeroormore = [label, zeroormore]
loneormore = [label, oneormore]
llookahead = [label, lookahead]
lnotlookahead = [label, notlookahead]
largument = [label, argument]
lprimary = [label, primary]
lspacing = [label, spacing]
lcomment = [label, comment]
lleftarrow = [label, leftarrow]
lslash = [label, slash]
larg = [label, arg]
lamp = [label, amp]
lbang = [label, bang]
lquestion = [label, question]
lstar = [label, star]
lplus = [label, plus]
lopen = [label, OPEN]
lclose = [label, close]
ldot = [label, dot]
lspace = [label, space]
leol = [label, eol]
leof = [label, eof]
llabel = [label, label]
lstring = [label, string]
lCLASS = [label, CLASS]
lchar = [label, char]
lindex = [label, index]
lnode = [label, node]

fp_ast = [
        main,
        [definition,
         [node, lmain],
         [sequence, lspacing, [oneormore, [argument, lexpr]], [choice, lparserun, leof]],
        ],
        [definition, [node, lparserun], [sequence, [string, 'parse_run'], lspacing]],
        [definition, lexpr, [argument, [choice, ldefinition]]],
        [definition,
         [node, lffdefinition],
         [sequence,
          [string, '```python'],
          lspacing,
          [argument, [sequence,
            [string, 'def'],
            lspacing,
            [argument, llabel],
            [zeroormore, [sequence, [notlookahead, [string, '`']], lchar]],
            [string, '```'],
          ]]
         ],
        ],
        [definition,
         [node, ldefinition],
         [sequence, [argument, [choice, llabel, lnode]], lleftarrow, [argument, lparseexpr]]
        ],
        [definition,
         lparseexpr,
         [choice,
          [argument, lchoice],
          [argument, lsequence],
          [choice,
           [argument, lzeroorone],
           [argument, lzeroormore],
           [argument, loneormore]
          ],
          [choice,
           [argument, llookahead],
           [argument, lnotlookahead],
           [argument, largument]
          ],
          [argument, lprimary]
         ],
        ],
        [definition,
         [node, lchoice],
         [sequence,
          [argument, [index, lparseexpr, 1]],
          [oneormore, [sequence, lslash, [argument, [index, lparseexpr, 1]]]],
         ],
        ],
        [definition,
         [node, lsequence],
         [sequence,
          [argument, [index, lparseexpr, 2]], [oneormore, [argument, [index, lparseexpr, 2]]],
         ],
        ],
        [definition, [node, lzeroorone], [sequence, [argument, [index, lparseexpr, 3]], lquestion]],
        [definition, [node, lzeroormore], [sequence, [argument, [index, lparseexpr, 3]], lstar]],
        [definition, [node, loneormore], [sequence, [argument, [index, lparseexpr, 3]], lplus]],
        [definition, [node, llookahead], [sequence, lamp, [argument, [index, lparseexpr, 4]]]],
        [definition, [node, lnotlookahead], [sequence, lbang, [argument, [index, lparseexpr, 4]]]],
        [definition, [node, largument], [sequence, larg, [argument, [index, lparseexpr, 4]]]],
        [definition, [node, lnode], [sequence, larg, [argument, llabel]]],
        [definition,
         lprimary,
         [choice,
          [sequence, lopen, [argument, lparseexpr], lclose],
          [sequence, [argument, llabel], [notlookahead, lleftarrow]],
          [argument, lstring],
          [argument, lCLASS],
          [argument, ldot],
          [argument, lindex],
         ],
        ],
        [definition,
         [node, lindex],
         [sequence,
          [argument, llabel],
          [string, ':'],
          [argument, [oneormore, [CLASS, '0-9']]],
         ],
        ],
        [definition, lspacing, [zeroormore, [choice, lspace, lcomment]]],
        [definition,
         lcomment,
         [sequence,
          [string, '#'],
          [zeroormore, [sequence, [notlookahead, leol], [dot]]],
          leol
         ]
        ],
        [definition, lleftarrow, [sequence, [string, '<-'], lspacing]],
        [definition, lslash, [sequence, [string, '/'], lspacing]],
        [definition, larg, [sequence, [string, '%'], lspacing]],
        [definition, lamp, [sequence, [string, '&'], lspacing]],
        [definition, lbang, [sequence, [string, '!'], lspacing]],
        [definition, lquestion, [sequence, [string, '?'], lspacing]],
        [definition, lstar, [sequence, [string, '*'], lspacing]],
        [definition, lplus, [sequence, [string, '+'], lspacing]],
        [definition, lopen, [sequence, [string, '('], lspacing]],
        [definition, lclose, [sequence, [string, ')'], lspacing]],
        [definition, [node, ldot], [sequence, [string, '.'], lspacing]],
        [definition, lspace, [choice, [string, ' '], [string, '\t'], leol]],
        [definition, leol, [choice, [string, '\r\n'], [string, '\r'], [string, '\n']]],
        [definition, leof, [notlookahead, [dot]]],
        [definition,
         [node, llabel],
         [sequence,
          [argument,
           [sequence,
            [CLASS, 'a-zA-Z_'],
            [zeroormore, [CLASS, 'a-zA-Z_0-9']],
           ],
          ],
          lspacing
         ],
        ],
        [definition,
         [node, lstring],
         [sequence,
          [choice,
           [sequence,
            [string, '"'],
            [argument, [zeroormore, [sequence, [notlookahead, [string, '"']], lchar]]],
            [string, '"'],
           ],
           [sequence,
            [string, "'"],
            [argument, [zeroormore, [sequence, [notlookahead, [string, "'"]], lchar]]],
            [string, "'"],
           ],
          ],
          lspacing,
         ],
        ],
        [definition,
         [node, lCLASS],
         [sequence,
          [string, '['],
          [argument, [oneormore, [sequence, [notlookahead, [string, ']']], lchar]]],
          [string, ']'],
          lspacing
         ],
        ],
        [definition,
         lchar,
         [argument,
          [choice,
           [sequence, [string, '\\'], [CLASS, 'nrt\'"\\']],
           [sequence, [string, '\\'], [CLASS, '0-2'], [CLASS, '0-7'], [CLASS, '0-7']],
           [sequence, [string, '\\'], [CLASS, '0-7'], [zeroorone, [CLASS, '0-7']]],
           [sequence, [notlookahead, [string, '\\']], [dot]]
          ],
         ],
        ],
]

#####################################################################
def lexString(text, idx, literal):
    if text.startswith(literal, idx):
        return idx + len(literal), [string, literal]
def lexDot(text, idx):
    if len(text) > idx:
        return idx + 1, [string, text[idx]]

# TODO get rid of re requirement
import re
def lexClass(text, idx, cclass):
    if re.search(f'^[{cclass}]', text[idx:]):
        return idx + 1, [string, text[idx]]

def lexSequence(text, idx, *args):
    c = [sequence]
    for a in args:
        if ( x:= a(text, idx)) is None:
            return None
        l, v = x
        idx = l
        c.append(v)
    return idx, c

def lexChoice(text, idx, *args):
    # return the first result that's not None
    return next((x for p in args if (x:=p(text, idx))), None)

def lexOneOrMore(text, idx, expr):
    c = [sequence]
    if (x:=expr(text, idx)) is None:
        return
    l, v = x
    idx = l
    c.append(v)
    while (x:=expr(text, idx)) is not None:
        l, v = x
        idx = l
        c.append(v)
    return idx, c
def lexZeroOrMore(text, idx, expr):
    c = [sequence]
    while (x:=expr(text, idx)) is not None:
        l, v = x
        idx = l
        c.append(v)
    return idx, c
def lexZeroOrOne(text, idx, expr):
    if (x:=expr(text, idx)) is None:
        return idx, [sequence]
    return x

def lexNotlookahead(text, idx, expr):
    if expr(text, idx) is None:
        return idx, [sequence]

def lexNode(text, idx, name, expr):
    if (x:=expr(text, idx)) is None:
        return
    l, v = x
    return l, [node, name, v]

def lexArgument(text, idx, expr):
    if (x:=expr(text, idx)) is None:
        return
    l, v = x
    return l, [argument, v]

def lexLabel(text, idx, name):
    if (x:=parser[name](text, idx)) is None:
        return
    l, v = x
    return l, [label, name, v]
    return parser[name](text, idx)

def lexIndex(text, idx, expr, offset):
    # TODO get rid of bare_args
    name = expr.args[0]
    if (x:=parser[name](text, idx, offset)) is None:
        return
    l, v = x
    return l, [label, name, v]

lexer = {
    string: lexString,
    dot: lexDot,
    sequence: lexSequence,
    choice: lexChoice,
    zeroormore: lexZeroOrMore,
    oneormore: lexOneOrMore,
    zeroorone: lexZeroOrOne,
    notlookahead: lexNotlookahead,
    argument: lexArgument,
    label: lexLabel,
    node: lexNode,
    CLASS: lexClass,
    index: lexIndex,
}
#####################################################################


#####################################################################

parser = {}
def ParseDefinition(lvalue, expr):
    """construct matching function from base expression."""
    kind, lvalue = lvalue
    if kind == node:
        _, lvalue = lvalue
        expr = [node, lvalue, expr]
    #print('defining', kind, lvalue)
    def prepLex(node):
        # TODO inject cache
        if not isinstance(node, (tuple, list)):
            return node
        name, *bare_args = node
        args = tuple(map(prepLex, bare_args))
        def prepped_lexer(text, idx, offset=0):
            #print(lexer[name].__name__, name, idx, *args)
            #print(name, *bare_args[offset:])
            out = lexer[name](text, idx, *args[offset:])
            #print(name, idx, bare_args[0] if bare_args else None, out)
            return out
        prepped_lexer.args = bare_args
        return prepped_lexer
    parser[lvalue] = prepLex(expr)


# TODO ARG should bind more tightly than STAR. it doesn't
EVAL = 'eval'
parse = 'parse'
boot = 'boot'
def evil(node):
    name, *args = node
    return ns[name](*args)

def Main(*top_level_expressions):
    for e in top_level_expressions:
        ns[EVAL](e)

def Parse(text, idx):
    if (x:=parser[main](text, idx)) is None:
        return
    _, v = x
    #v = trim(v)
    v = trim(v)
    return v

def trim(x, ancestor=None, memo=None):
    match x:
        case [trim.node, name, body]:
            memo = []
            trim(body, node, memo)
            return [name, *memo]
        case [trim.argument, body]:
            body = trim(body, argument, memo)
            memo.append(body)
            return body
        case [trim.label, name, body]:
            if ancestor == argument:
                return trim(body, ancestor, [])
        case [trim.string, literal]:
            if ancestor == argument:
                return literal
        case [trim.sequence, *args]:
            args = [trim(a, ancestor, memo) for a in args]
            if ancestor == argument:
                out = []
                while args:
                    a = args.pop(0)
                    match a:
                        case [trim.sequence, *args2]:
                            args = args2 + args
                            #out.extend(args2)
                        case str():
                            if isinstance(out and out[-1], str):
                                out[-1] += a
                            else:
                                out.append(a)
                        case _:
                            out.append(a)
                if len(out) == 1:
                    return out[0]
                return [sequence, *out]
        case [typ, *args]:
            out = [trim(a, ancestor, memo) for a in args]
            if ancestor == argument:
                return [typ, *out]
        case x:
            return x

# fuckery to make pattern matching work
trim.node = node
trim.argument = argument
trim.label = label
trim.string = string
trim.sequence = sequence

def Boot(input_text, init_ast=None):
    if init_ast:
        print('loading grammar')
        ns[main](init_ast)
    print('grammar loaded')
    pp(Parse(input_text, 0))
    #ast = ns[parse](input_text, 0)
    #print(ast)

ns = {
        boot: Boot,
        main: Main,
        EVAL: evil,
        definition: ParseDefinition,
        parse: Parse,
}
input_text = """
Expr    <- Sum
Sum     <- Product (('+' / '-') Product)*
Product <- Power (('*' / '/') Power)*
Power   <- Value ('^' Power)?
Value   <- [0-9]+ / '(' Expr ')'
"""
#ns[EVAL](fp_ast)
input_ast = [main,
    [definition,
     [node, lCLASS],
     [sequence,
      [string, '['],
      [argument, [oneormore, [sequence, [notlookahead, [string, ']']], lchar]]],
      [string, ']'],
      lspacing
     ],
    ],
]
#print(lexDot(input_text, 6))
input_text = """awful <-  bashful"""
input_text = "%Class <- '[' %(!']' Char)+ ']'"
ns[boot](input_text, fp_ast)
print()
input_text = """awful <- '[' bashful"""
ns[boot](input_text, fp_ast)
