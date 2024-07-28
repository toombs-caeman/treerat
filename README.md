# treerat

This is a language for rapidly prototyping domain specific languages (DSLs) hosted within a general purpose language (GPL).

It works by exposing a self-modifying parser and interpreter that can call or define methods in the host language while allowing total syntactic freedom. The heavy lifting of semantics can be handled by the host.

The initial language is intentionally simple, only able to modify itself.

It works by starting with a minimum viable language (MVL) that can only modify its own parser and interpreter or define new functions in a host language.

* [original inspo](https://blog.bruce-hill.com/packrat-parsing-from-scratch)
# current status
version 0.1 initial implementation phase

Error handling & reporting needs to be better. The parser to interpreter loop needs to be tightened up.


# the initial language
The parser is a packrat parser with a modifiable internal representation of the current grammar and the remaining input.

# MVL design considerations
* The implementation should be small and straightforward above all else. I want the MVL to be as easy to understand and to hack as possible.
* don't use fancy language features to implement the MVL. It should be a nearly one to one translation to any another host language.
* the abstract syntax tree (AST) emitted by the MVL parser is a list of lists and strings. Every list is a node, and the first item of every list is a string that indicates that node's type. It is up to the interpreter to resolve those names. This is probably not very performant, but it simplifies booting up the parser.
* performance doesn't matter much. "Worse" code which is easier to read is prefered.

# MVL internals
The abstract syntax tree (AST) emitted by the MVL's packrack parser is a list of lists and strings. Every list is a node, and the first item of every list is a string that indicates that node's type. It is up to the interpreter to resolve those names.

The MVL's interpreter resolves the top level node's name in a flat namespace of functions, then evaluates that function with the other items in that node as arguments. The top level node is usually "Main", which evaluates a list of statements in order by resolving the node name and evaluating the resulting function in the same way.

MVL boots by evaluating a pre-parsed AST that loads the initial grammar into the parser and then tries to parse new input.

The grammar modification syntax is based on [parsing expression grammars](https://en.wikipedia.org/wiki/Parsing_expression_grammar) but with extensions in order to specify which elements are purely syntactic and which should be present in the resulting parse tree.

The foreign function syntax allows functions to be written in the host language and added to the internal namespace.

## initial interpreter data
Some core data must be pre-loaded into the parser and interpreter for them to function.
The parser needs an initial grammar, and the interpreter needs an implementation of that grammar and a reference to the parser.

initial interpreter functions
* boot - loads input, calls main while there are no errors
* main - runs the parser, evaluates the parse tree.
* ffi - load host function into interpreter namespace
* clear - empty the grammar
* update - update the grammar
* swap - return control to the parser. Updates to the grammar do not apply until the swap.
* parse - a reference to the parser

derivative functions
* eval - define function in host, then load through ffi
* pause - save the current state of the interpreter such that it can be restarted. (execution will restart at boot function)

# Grammar
from https://bford.info/pub/lang/peg.pdf
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

# grammar version
as a hash of the grammar?
as a hash of the host + grammar + primitives?

# internal representation & intermediate representation
* grammar - a name only representation of the current grammar rules
* ast - output by the parser, valid json


* grammar (in parser)
* parse tree representation (must be shared by parser and interpreter)
* name resolution (in interpreter) including parser and interpreter

* markers - index into the input

* match constructor phase
    * parsedefinition -> matcher function
* matching phase
    * raw text + matcher function -> node + children + markers
* trim phase - remove nodes not marked as arguments
    * node + children + markers -> ast

# why
I was playing with packrat parsing one day and I thought it would be easy.
It is not, but writing a language is pretty fun.

I have a bunch of ideas for 'micro' languages which would be greatly aided by this.

* a sane shell language, built on an insane foundation
    * using posix `sh` as a runtime
    * a session thats able to seamlessly transfer itself over ssh, even if the shell isn't 'installed' on the new host
* a parsing language
* a templating language
  * [moustache](https://mustache.github.io/mustache.5.html) templating
  * [jinja](https://jinja.palletsprojects.com)
  * python's [f-string](https://peps.python.org/pep-0498/)

* data format
  * [TOML](https://github.com/toml-lang/toml)
  * [YAML](https://yaml.org/), or pseudo-INI
  * [Tablatal / Indental](https://wiki.xxiivv.com/site/tablatal.html)

* a data query format
  * [dasel](https://github.com/TomWright/dasel)
  * [gron](https://github.com/tomnomnom/gron) for grepping json

# examples

```
Expr    ← Sum
Sum     ← Product (('+' / '-') Product)*
Product ← Power (('*' / '/') Power)*
Power   ← Value ('^' Power)?
Value   ← [0-9]+ / '(' Expr ')'
```
This snippet defines how to parse algebraic expression using the normal precedence rules.
# roadmap
* version 0.1
    * python host: parser, ffi, peg, 
* version 0.2
    * python host: eval, purge
* version 0.3
    * javascript host
* version 0.4
    * language server protocol, syntax highlighting??
* version 0.5
    * c/c++ host
* version 1.0
    * standalone interpreters/semantics?

# parse debugging
* detect mutual left recursion as a value error for parsers
* point out probable syntax errors when failing to parse

# features to play with later
* embed debug visualization types as an extension of debug symbols
    * how should utilization of a function be visualized in a debugging context?
    * expected data size?
    * expected runtime? to flag functions that are underperforming
* inline snapshot testing
* can name everything, don't have to name anything
    * DeBrujin naming
    * [name resolution](https://willcrichton.net/notes/specificity-programming-languages/)
* optimization modes
* reversible parse expressions?
* name resolution
    * scoping, garbage collection, var lifetimes
* representing state machines such that transition diagrams can be automatically generated, and properties statically analyzed?
* 'return a mutation object' as a model for 'pure' functions with the program state as input, and a new state as output. (equivalent to transactions?)
* trait-based type heirarchy
* language language to sql (python+sql+apl)
* packages published as source under git, use semver git tags to publish version so there's no separate packaging mechanism. The package name is the host url (sans http://)
* toolchain/compiler/interpreter/linter/etc should be a single binary file
* how to resolve incompatible libraries? do we allow multiple versions of the same libraries. how can we have 'virtual env' to capture the dependencies of just the current project in a separate tree.
* a 'binary' is a frozen and trimmed program state (trim to reachable code from entry point and exec) or have multiple entrypoints bundled like busybox
* shebang convention to automatically run source file as an interpreter (as bash does).
* language primitives exposing heap/stack differences, or other low level concepts should not be 'default'. The default numeric type should be bignum, but let `u32` be specified. default sequence type should be a vector (variable size/type), but allow array (const size, uniform type) be specified.
* separate language into high and low level primitives, high level primitives are expressible multiple ways using low level primitives, chosen by static analysis and optimization level (for example [] would mean 'any sequence' unless given an explicit annotation, depending on usage it could compile to array or a vector).
* high level types are collections of traits, any low level structure which implements those traits may be used at compile time
* a type should be capable of reflecting any arbitrary rules a programmer knows about the bounds of a value (integers in range, 0<=float<1)
    * bounded number types (aka enums, but not necessarily enumerable)
        * let x be a float in [0, 1]. on cast from float, clamp
        * let y be an int [0, 8). on cast from int, mod 8
        * let bool be int 0 or 1. on cast from float, fail
    * typed strings for embedded langauges, with custom value escaping / formatting
        * regex
        * sql queries
        * these are used as special form literal values, but cannot be checked by the type system because the cast from string is usually implemented by a library
* interface driven types
* [comptime](https://kristoff.it/blog/what-is-zig-comptime/)
* embed sqlite in the language
* use python's taxonomy of [collections](https://docs.python.org/3/library/collections.abc.html#collections-abstract-base-classes)
* consise lambda function
* function lifting
    `obj.{a,b,c}` returns dict {'a':obj.a, 'b':obj.b, 'c': obj.c}
    `obj.[a,b,c]` returns list ['a':obj.a, 'b':obj.b, 'c': obj.c]

* rewrite it in forth?
* rewrite it in rust
    * native types: null, int, float, complex, string, map, set, list, matrix

# forth implementations
* [jonesforth](https://github.com/nornagon/jonesforth/blob/master/jonesforth.S)
* [lina forth](http://home.hccnet.nl/a.w.m.van.der.horst/lina.html)
* [gforth](https://en.wikipedia.org/wiki/Gforth)
* fig-Forth
* F83
# reference
* [programming language design](https://toombs-caeman.github.io/pl)
* [scrapscript](https://scrapscript.org/)
    * content addressable code
* [katahdin](https://chrisseaton.com/katahdin/)
* [syntax across languages](http://rigaux.org/language-study/syntax-across-languages.html)
* [minima](https://github.com/TheRealMichaelWang/minima)


# [AoC language noulith](https://blog.vero.site/post/noulith)
    * `.` and `then` as reverse funtion application
    * match expression implicitly declares vars
    * `_0`, `_1` to implicitly create lambdas with positional arguments
* [general purpose languages](https://en.wikipedia.org/wiki/General-purpose_programming_language)
* [function composition](https://hackage.haskell.org/package/base-4.17.0.0/docs/Control-Arrow.html)

* [packrat reference](https://bford.info/packrat/)
* [function lifting (automap)](https://futhark-lang.org/blog/2024-06-17-automap.html)
* [crafting interpreters](https://craftinginterpreters.com/)

* [python builtins](https://docs.python.org/3/library/functions.html)
* [python itertools](https://docs.python.org/3/library/itertools.html)
* [bqn](https://mlochbaum.github.io/BQN/tutorial/expression.html)
* [elixir](https://learnxinyminutes.com/docs/elixir/)
* [eff lang](https://www.eff-lang.org/) (OCaml + algebraic effects)

[regex-vis](https://regex-vis.com/?r=%2F%5E%28%28%5BhH%5Dacker%29%5B+%5D%3F%28%5BnN%5Dews%7Cnewsletter%29%29%24%2F)
[discussion regex-vis](https://news.ycombinator.com/item?id=31307123)
[regex101](https://regex101.com/)

* [semantic versioning](https://semver.org/)
