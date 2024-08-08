# treerat

This is my exploration of [programming language design](https://toombs-caeman.github.io/pl).

The goal of the project is just to explore ideas as they occur to me and not necessarily develop a viable language.
However, I intend to eventually build enough components that this becomes a useful toolkit for exploring novel languages.

In this initial stage, I am focusing on high-level theory, readability, and visualizations rather than efficiency.
Eventually I will implement, as an example, the same language in python and rust/c99 with the goal of a self hosting language.
The python implementations will continue to focus on readability while the lower-level will focus on efficiency.

# Language Components
The following language components can be considered higher order functions that are generic over the precise language being implemented.
My goal here is to implement the components such that they can be easily extended to implement any target language.

Only a few of these have actually been completed.

* parser (source code -> ast)
    * a tokenizer is a vastly simplified form that parses source into a flat list of strings (tokens)
* tree IR
    * compiler (tree -> tree) (can be noop)
    * static analysis (tree -> status) (can be noop)
        * do all node kinds have implementations?
        * do all nodes match number of arguments to implementation arity?
        * type checks, do all the node arguments have an expected type?
    * optimizer (tree -> tree) (can be noop)
        * type inference, do we need to insert casts?
        * can we statically evaluate some branches?
    * evaluators (tree -> action)
* bytecode IR
    * compiler (ast -> bytecode)
    * static analysis (bytecode -> status) (can be noop)
        * do all bytecodes have implementations?
        * are all const references valid?
    * optimizer (bytecode -> bytecode) (can be noop)
        * can we statically evaluate some operations?
    * evaluator (bytecode -> action)
* graph IR
    * compiler (ast -> graph)
    * static analysis (graph -> status) (can be noop)
        * do all bosons have implementations?
        * are there cycles?
    * optimizer (graph -> graph) (can be noop)
        * can we transpile hot paths?
        * can we autothread?
        * can we statically evaluate some bosons?
    * transpiler (graph -> bytecode)
    * evaluator (graph -> action)
* loader
    * how do we get data into the toolchain?
        * loading source files
        * loading intermedite artifacts (IR). What is the on-disk representation?
        * fetch libraries from urls? expect them at a hardcoded file location?

* [compiler drivers](https://fabiensanglard.net/dc/index.php) - the user interface for a language
    * bind together a specific grammar, parser, analyzer, optimizer, loader and evaluator into a complete language toolchain
    * REPL?


# Visualization
Pygraphviz is used to visualize tree and graph structures.
Computation can be visualized through a small extension to render animated gifs.
The basic evaluators are instrumented to automatically generate these visualizations as they run.

Visualization tools are in `viz.py`

TODO:
* figure out how to text animations in combination with graphviz (render to html?)
* I'd love to be able to have source, ast (graphviz), bytecode, vm state (stack + registers) all side by side,
    with an animation to step through execution and highlights linking the active segment of each representation.
    * render this as an html fragment that I can include in my blog
    * use javascript to allow controls: run, pause, reverse, step
    * with a wasm backend for the language components, you could actually just develop a new language server-side in the browser
    * [viz.js](https://github.com/mdaines/viz-js)

# Parser

`parser.py` contains a generic packrat parser.

It can initialize its grammar from an abstract syntax tree (AST) or text, but uses a "fixedpoint" grammar by default.
If a language specification is given as a string, it will be parsed according to the fixedpoint grammar
and the resuting AST will be used to initialize the parser as normal.

The fixedpoint is named as such because parsing the fixedpoint grammar with a fixedpoint parser
produces a syntax tree which can directly initialize an identical parser.

The fixedpoint language itself is a small extension of the Parsing Expression Grammar (PEG).

[read more](parser.md)

# Name resolution
TODO
* IR agnostic name resolution for lexical scoping?
* crafting interpreters page 173 for an example of pathological scope. make sure the reference implementations get it right
    * closures too

see also:
* [wikipedia](https://en.wikipedia.org/wiki/Name_resolution_(programming_languages))

# Type and Effect Systems
TODO: IR agnostic type inference implementation.

[read more](types.md)

# Graph Intermediate Representation (GIR)
Exploration of using a directed graph structure to model data dependency and flow through the program.
My intuition is that graph algorithms offer a natural way to approach optimizing programs and introducing novel features
such as implicit multithreading.

In this model, "bosons" (nodes) are units of computation and "fermions" (edges) are "productions" or
"temporal dependencies" which form relations between bosons.

Before any evaluation, fermions exist in a superposition, being neither True or False.
A boson may only begin evaluation if all of its incoming edges are True (or if it has none).
This ensures that all dependencies are fulfilled and all incoming values exist.
When a boson finishes evaluation, it marks each outgoing edge as True or False and potentially sets its value.

Fermions are typed. They may represent a value (of a given type), a mutation, an exception,
or anything else that would be considered a 'side effect' or 'external effect' in another context.
They can also simply represent temporal ordering, rather than any native value of the language. Such constraints can
be introduced by the language to enforce total ordering of effects when appropriate, eliminating race conditions.
Boson evaluation is rendered pure by considering any possible side-effect as fermions.

Since effects are represented as edges, we must have a special node "SINK" which consumes all uncaught effects.
During manipulation of the graph this is considered a node to make the graph well formed.
However, it doesn't have the same scheduling flexibility as a boson and must always evaluate effects in the exact order they are produced

Correct programs must be acyclic.
Loops are still possible to represent, but as a subgraph which is instantiated (reset) for each iteration.

[see more](dag.md)

# Evaluators
An evaluator can be thought of as embodying the semantics of a language. In slightly more concrete terms, evaluators do
the computations described by a given IR.

Of course, the simplest evaluator is a tree-walk interpreter.

I have yet to build any evaluator of the GIR.

# grammar version
as a hash of the grammar?
as a hash of the host + grammar + primitives?

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

# reference
* forth implementations
    * [jonesforth](https://github.com/nornagon/jonesforth/blob/master/jonesforth.S)
    * [lina forth](http://home.hccnet.nl/a.w.m.van.der.horst/lina.html)
    * [gforth](https://en.wikipedia.org/wiki/Gforth)
    * fig-Forth
    * F83
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
* erlang/beam
* [weathering the software winter](https://100r.co/site/weathering_software_winter.html) a discussion of why you might want to be fully in control of your software stack.

# TODO
* jank around the definition of the fixedpoint and interactions between Argument and OneOrMore,etc.
* type system
* grammar registry
