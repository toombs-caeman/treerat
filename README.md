# treerat

This is a language for rapidly prototyping domain specific languages (DSLs) hosted within a general purpose language (GPL).

It works by exposing a self-modifying parser and interpreter that can call or define methods in the host language.

The initial language is intentionally simple, only able to modify itself.

# current status
version 0.0 design phase

The parser sort of works, but not in a form that's self-modifiable.
This is more a thought experiment than anything.

# the initial language
The parser is a packrat parser with a modifiable internal representation of the current grammar and the remaining input.
The grammar modification syntax is based on [parsing expression grammars](https://en.wikipedia.org/wiki/Parsing_expression_grammar) but with extensions in order to specify which elements are purely syntactic and which should be present in the resulting parse tree.

The parse tree is passed to a basic interpreter, which maps nodes types to functions in the host language and immediately evaluates them. When evaluation finishes, control is passed back to the parser. It is possible to hotswap the parser and/or interpreter by updating their mutual references.


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

# reference
* [syntax across languages](http://rigaux.org/language-study/syntax-across-languages.html)


# [AoC language noulith](https://blog.vero.site/post/noulith)
* `.` and `then` as reverse funtion application
* match expression implicitly declares vars
* `_0` or `` `0 `` to implicitly create lambdas with positional arguments
* [general purpose languages](https://en.wikipedia.org/wiki/General-purpose_programming_language)
* [function composition](https://hackage.haskell.org/package/base-4.17.0.0/docs/Control-Arrow.html)
* use a tree rat as the mascot (red crested tree rat?)
