
`parser.py` contains a generic packrat parser.

It can initialize its grammar from an abstract syntax tree (AST) or text, but uses a "fixedpoint" grammar by default.
If a language specification is given as a string, it will be parsed according to the fixedpoint grammar
and the resuting AST will be used to initialize the parser as normal.

The fixedpoint is named as such because parsing the fixedpoint grammar with a fixedpoint parser
produces a syntax tree which can directly initialize an identical parser.

The fixedpoint language itself is a small extension of the Parsing Expression Grammar (PEG), which adds two operators.
* `%` allows the language to specify which symbols to retain in the output,
      and which should generate nodes in the resulting abstract syntax tree.
* `:` allows more convenient construction of operator precedence but is only syntactic sugar, strictly speaking.

For example take the following grammar, which recognizes one or more math expressions separated with semicolons:
```
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
```

On the left hand side of a definition, `%` denotes that the symbol generates a node in the output.
Non-terminal symbol definitions which lack a `%` are used only as labels for use in other definitions,
and do not represent nodes in the output.
As we can see, the output of parsing this grammar may contain nodes of kind start, Add, Sub, Mul, Div, Float, and Int.

On the right hand side `%` designates that a symbol should be retained as an argument in the output.
In the definition of Add, there are two arguments marked with `%` which must always match to successfully match Add,
so the output node Add will always have two children. PLUS must also match in the process of matching Add,
but the contents of PLUS are always discarded because it was not marked with `%` (its contents are empty anyway).
In the definition of Div, the second argument may be repeated one or more times because the `+` operator encloses `%`,
therefore Div nodes have two or more children.
Expr only ever has one arguement because, while `%` is used a few times, only one `%` expression will match at a time.
Because Expr does not designate a node, the matched argument will be substituted directly in definitions where Expr
is referenced, rather than encapsulating the argument itself.

`:` refers to an implicit symbol based on an explicit definition.
`Expr:1` means to take every term of Expr except the first. In this case it is equivalent to the following:
`Expr:1 <- (%Mul / %Div) / %Float / %Int / '(' %Expr ')'`
The purpose of `:` is to make operator precedence easier to express.
Some choices in Expr are grouped, even though an ungrouped choice is locally equivalent, to express that those
operators have equal precedence.

# Fixed Point Grammar
modified from the [original paper](https://bford.info/pub/lang/peg.pdf)
```
%main <- Spacing %Definition+ EndOfFile
%Definition <- %Identifier LEFTARROW %Expression
Expression <- Choice /
    Sequence /
    (ZeroOrOne / ZeroOrMore / OneOrMore) /
    (Lookahead / NotLookahead / Argument) /
    Identifier !LEFTARROW /
    OPEN Expression CLOSE /
    Literal /
    Class /
    DOT
%Choice   <- Expression:1 (SLASH Expression:1)+
%Sequence <- Expression:2 Expression:2+
%ZeroOrOne  <- Expression:3 IBANG
%ZeroOrMore <- Expression:3 STAR
%OneOrMore  <- Expression:3 PLUS
%Lookahead    <- AMP  Expression:4
%NotLookahead <- BANG Expression:4
%Argument     <- CENT Expression:4
%Identifier <- %[a-zA-Z_] %[a-zA-Z_0-9]* Spacing
%Literal <- ['] (!['] Char)* ['] Spacing / ["] (!["] Char)* ["] Spacing
%Class <- '[' %(!']' (Range/Char))* ']' Spacing
%Range <- %Char '-' %Char
Char <- %('\\' [nrt'"\[\]\\]
    / '\\' [0-2][0-7][0-7]
    / '\\' [0-7][0-7]?
    / !'\\' .)
LEFTARROW <- '<-' Spacing
SLASH     <- '/' Spacing
CENT      <- '%' Spacing
AMP       <- '&' Spacing
BANG      <- '!' Spacing
IBANG     <- '?' Spacing
STAR      <- '*' Spacing
PLUS      <- '+' Spacing
OPEN      <- '(' Spacing
CLOSE     <- ')' Spacing
%DOT      <- '.' Spacing
Spacing   <- (Space / Comment)*
Comment   <- '#' (!EndOfLine .)* EndOfLine
Space     <- ' ' / '\t' / EndOfLine
EndOfLine <- '\r\n' / '\n' / '\r'
EndOfFile <- !.
```

# c implementation notes
* there are typically only a small amount of kinds < 128, use one byte.
    * 7bit id and 1 bit for oldkind or newkind
* use two bytes to indicate number of children
* children are just pointers to other spots on the heap
* string kind can pair of pointers to start and end

## cache
there will be 100~500 rules and for each index of the input, need to know if a rule has been applied there.
* need to keep a hashmap (ruleptr,index) => resultptr or nullptr
    if input length < 2^32 characters

If there are fewer than 32 or 64 rules

# conclusion

TODO:
* some ideas from [rust-peg](https://docs.rs/peg/latest/peg/)
    * inline argument names, rather than  positional args with `%`
    * line implementation for rules (not sure this is productive)
    * inline implementation for conditional matching
    * `expr**delim` and `expr++delim` repeated match with delimiter
    * `<n,>`, `<,m>`, `<n,m>` match between n and m repetitions
    * inline expected value to show what should have been there for parsing to proceed further.
    * explicitly choose when a rule should be cached. Simple rules may be faster to re-match than to do a hash table lookup

* detect mutual left recursion in a grammar and refuse to initialize
* provide partial parsings and extended error reporting. Use [pika parsing](https://github.com/lukehutch/pikaparser)?
* could a language define grammars by name/hash, pull them from a repository?
* binary grammar format, a 'compiled' grammar
* what can we learn from [how regex expressions are compiled?](https://github.com/codecrafters-io/build-your-own-x?tab=readme-ov-file#build-your-own-regex-engine)

see also:
* [PEG wikipedia](https://en.wikipedia.org/wiki/Parsing_expression_grammar)
* [PEG original paper](https://bford.info/pub/lang/peg.pdf)
* my [inspiration](https://blog.bruce-hill.com/packrat-parsing-from-scratch)
* [golang regex from scratch](https://rhaeguard.github.io/posts/regex/)
