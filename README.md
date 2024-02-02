# treerat

This is a language for rapidly prototyping domain specific languages (DSLs) hosted within a general purpose language (GPL).
It works by starting with a minimum viable language (MVL) that can only modify its own parser and interpreter or define new functions in a host language.

# current status
version 0.1 initial implementation phase

Error handling & reporting needs to be better. The parser to interpreter loop needs to be tightened up, and there seem to be some bugs in the initial AST.

# MVL design considerations
* The implementation should be small and straightforward above all else. I want the MVL to be as easy to understand and to hack as possible.
* don't use fancy language features to implement the MVL. It should be a nearly one to one translation to any another host language.
* the abstract syntax tree (AST) emitted by the MVL parser is a list of lists and strings. Every list is a node, and the first item of every list is a string that indicates that node's type. It is up to the interpreter to resolve those names. This is probably not very performant, but it simplifies booting up the parser.
* performance doesn't matter much. "Worse" code which is easier to read is prefered.

# MVL internals
The abstract syntax tree (AST) emitted by the MVL's packrack parser is a list of lists and strings. Every list is a node, and the first item of every list is a string that indicates that node's type. It is up to the interpreter to resolve those names.

The MVL's interpreter resolves the top level node's name in a flat namespace of functions, then evaluates that function with the other items in that node as arguments. The top level node is usually "Main", which evaluates a list of statements in order by resolving the node name and evaluating the resulting function in the same way.

MVL boots by evaluating a pre-parsed AST that loads the initial grammar into the parser and then tries to parse new input.

# MVL syntax
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

# grammar version
as a hash of the grammar?
as a hash of the host + grammar + primitives?

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

# name options
* [ayeaye](https://subnautica.fandom.com/wiki/Eyeye)
* [minima](https://github.com/TheRealMichaelWang/minima)
* use a tree rat as the mascot (red crested tree rat?) because its a tree walk interpreter and packrat parser

# reference
* [syntax across languages](http://rigaux.org/language-study/syntax-across-languages.html)


# [AoC language noulith](https://blog.vero.site/post/noulith)
    * `.` and `then` as reverse funtion application
    * match expression implicitly declares vars
    * `_0`, `_1` to implicitly create lambdas with positional arguments
* [general purpose languages](https://en.wikipedia.org/wiki/General-purpose_programming_language)
* [function composition](https://hackage.haskell.org/package/base-4.17.0.0/docs/Control-Arrow.html)
* [python builtins](https://docs.python.org/3/library/functions.html)
* [python itertools](https://docs.python.org/3/library/itertools.html)
* [bqn](https://mlochbaum.github.io/BQN/tutorial/expression.html)
* [elixir](https://learnxinyminutes.com/docs/elixir/)
