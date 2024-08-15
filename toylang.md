A description of a (not yet named) language which I would like to build.

The purpose of this language is to develop ideas around the graph intermediate representation ([GIR](dag.md)), type inference, and implicit threading.

# General Semantics
Code is a textual description of Computation.
Computation produces one or more Effects when run, through the application of Functions to Values.

Effects are not Values.
An Effect is any externally visible change that results from doing the Computation.
"produce a Value" is an Effect, as is "raise an Error" or "mutating a Value".

Values do not exist in Code.
There are only Literals which are text that describe Values by implicitly or explicitly being assigned Traits.

Functions are Values which implement a Computation.
Functions do not exist in Code (they are Values).
Functions may be applied to any set of Values which match the Traits defined by the Function's arguments.
Functions may only produce Effects matching the traits it specifies.
A Function application is not required to produce all Effects the Function is capable of producing.

Casts are Functions with the special Trait that their result is considered equivalent to their input in all cases. Thus Casts can be implicitly inserted into any Computation even when not described by the Code.

Types are Values used to produce a Value from a Literal. They can be considered a specialized Function.
Types do not exist in Code (they are Values).
Any Type which implements all Traits assigned to a Literal may be used to instantiate a corresponding Value.
There may be more than one available Type but it is an Error for there to be no available Types for any given Literal.
A Value is said to be 'an instance of' or simply 'of' a Type if it created from that Type.
All Values are an instance of exactly one Type.

When more than one Type is assignable to a Literal, Types are selected according to a heuristic which uses the most efficient available Type and which minimizes Casts.

A Function application can only "be applied" when all of the input values (including the Function to be applied) have been produced.
A Function only needs to be applied if it has the possibility of producing an Effect.
There's no point in doing work that will not cause externally visible changes.

# graph semantics
Control flow is nodes and values are edges. Node type determines when a node can be scheduled. Only three real types, loop, branch, and apply.
node types:
* loop,break - allow some self loops, where each iteration depends only on preceeding iterations (re-instantiation of subgraphs)
* branch,join - conditional is ready, branches as subgraphs

* apply,return - all incoming edges are ready
* raise,try,catch - all incoming edges are ready, not special, just consumes an unusual effect
* input,output - immediate when all incoming edges are ready, but may sleep before producing values

# Specifics
Given these semantics, an implementation of this language requires a few parts:
* a way to parse Code into a network of Literals and Function applications, connected by their potential Effects.
    * text parsing, name resolution, trait propogation, transformation to GIR
* a scheduler that selects the next function to apply in order to possibly produce effects
* an Interpreter that applies functions selected by the scheduler
* a selection of native Types, Traits, Casts, Effects and Functions.
* an interface for defining new Types, Traits, Casts, Effects and Functions.

* compiler: Code -> tree -> graph -> optimal graph -> disk
* runtime: disk -> graph -> Effects

# Core Traits
* callable - that which can be applied (functions, types, etc.)
    * input - a callable which relies on external input
    * output - a callable which produces effects external to the program
    * totalorder(x...) - causes race conditions unless there is a total ordering of all computations x...
    * commutative(x) - f(a,b) === f(b,a)
    * associative(x) - f(a, f(b, c)) === f(f(a,b), c) which enables some graph re-writes for better parallelism
    * distributive(x,y) - [distributive](https://en.wikipedia.org/wiki/Distributive_property)
    * [category of properties of binary operations](https://en.wikipedia.org/wiki/Category:Properties_of_binary_operations)
    * [magma](https://en.wikipedia.org/wiki/Magma_(algebra))
    * identity and inverse elements
* container(x) - can determine if a value of type x exists in the container Value
    * enumerable(x) - container can produce a sequence of zero or more values of type x. It has a length (size)
    * mapping(x,y) - container produces y for every x in container
    * sortable - true if enumerable(x) and x implements comparable(x)
    * insert(x) - can add x to container
    * remove(x) - can remove x from container
* maxlen(int) - container has a maximum number of contained items
* queue(x) - represents a fifo queue, not necessarily container(x) or enumerable(x)
* stack(x) - represents a filo stack
* hasattr(x) - a Value has a named attribute x
* comparable(x) - a Value can be compared to type x
* isvalue(x) - a Value is statically determinable
* cast(x) - Value can be cast to type x
* cast(bool) - a Value can be considered True or False
* hashable - a Value can be hashed, specialization of cast(int)
* threadsafe - a value can be safely shared between threads
* numeric - a number
    * int - an integer
        * int8, int16, int32, int64, ...
        * uint - an unsigned integer
            * uint8, ...
    * float - an IEEE floating point number
        * f32, f64, ...
    * complex - a complex number
* controlflow - a function which receives its arguments unevaluated
* persist - a value can persist itself to disk

# core types
* set[V:hashable]: container[V]
* hashmap[K:hashable,V]: enumerable[K], mapping[K,V]
    * valueview: enumerable[V]
* list[V]: enumerable[V]
* ndarray[shape]: enumerable[numeric] - implements vector math and broadcasting like numpy

* rune - a single unicode (utf-8) character
* string: list[rune]

* range: enumerable[int]
* int
* float
* complex
* bool: int[0]|int[1]

* byte: int8
* bytearray: list[byte]

* chan[X]: threadsafe, queue[X]
* regex?

* function
* exception

* branch,join: controlflow
* loop,break: controlflow
* apply: controlflow
* raise: controlflow
* try,catch: controlflow
control flow receives subgraphs as arguments, rather than other values.

# special syntax
* fstring - `f'{x} {y}'` => `cast_string(x) + ' ' + cast_string(y)`

* function application
    * `x.sort()` looks for any function named `sort` with trait receive[type(x)] or receive[Y:rcast[type(x)]]
    * if used as a statement, `x.sort()` => `x = sort(x)`
        * if it is efficient to do so and the value is not shared, this may actually sort in place
    * if used as an expression `x.sort()` => `sort(x)`

* pattern matching assignment
* aliasing - solving systems of equations?
# special properties
leave it to the compiler to decide:
* whether or not a function modifies a value in place or returns a new value.
    * `x.sort()` === `x = x.sort()` (=== `y = x.sort()` iff `x` is not accessed afterwards)
    * whether a value is *really* mutable or not doesn't matter.
* where it is efficient to thread code
* where to cast
* how to make code cache efficient
* what to compute at comptime, vs runtime.
* value lifetimes

* which input functions are applied at comp time and which are 'deferred' to runtime?
    * let the full language be available at compile time
* function lifting (implicit map over arguments of unexpected rank)

# examples
* a literal `10` has trait "numeric", but that trait is fulfilled by any int, float or complex type.
    * a literal `1.2` has traits "numeric" and "float", so cannot be implemented by an int.
    * the expression `1 + 0.2` has traits numeric and float. since `1` may be implemented by int or float, it will be implemented as float in order to avoid a cast from int to float before `+`
* a literal function application `sort(x,y)` has traits "callable", "named(sort)", and "receives(type(x), type(y))"
    * may be called as `x.sort(y)`

# orthogonal syntax
unify parts of programming languages that are typically similar but different syntax.

for..in, foreach, and map are closely related keywords across many different languages.
All use cases of these are served by the singular loop.
Loop also handles the need for while, do..while, reduce and filter.
Similarly, branch handles the need for if, else, and case keywords

rather than special syntax for generics and macros let the full language be available at compile time

# borrowing features
'borrow' successful features and workflows from other languages.
golang
* channels - typed thread-safe fifo as only communication between threads
* fmt - standard toolchain includes linter/formatter
* get (library name indicates fetch url)
* static binaries for easy containerization.
rust
* borrow (reference) and scoping semantics to get around gc
apl
* function semantics
sql
* the same code can lead to different 'plans' at runtime based on meta-data about the execution context or data size
zig
bash et al.
* allow source files to run in 'interpreter mode', or have a repl
python
* allow deep destructured assignment
* whitespace significant
* slice syntax
elixir
* assignment is actually pattern matching


# core syntax v0.1
literal types
* numbers and infinity
* string ''
* regex ` `
* fstring ""
* pair :
* signature/ast pattern <>
* set {}
* list []
* block ()
* iterator *
* pair iterator `**`
* range iterator ..

names (variables)
* name `[a-zA-Z][a-zA-Z_]*`
* assign =

literal functions
* math operators +(add) -(sub) `*`(mul) /(div) //(idiv) !/(mod) ^(exp) /^(log)
* unary math    +(abs) -(inv) !^(factorial???)
* bool operators !(not) /+(or) `/*`(and) /-(xor) !+(nor) `!*`(nand) !-(xnor)
* comparators /=(eq) /<(lt) />(gt) !=(ne) !<(nl) !>(ng)
* object operator .(access) !.(safe access) `_`(typeof) `/_`(isinstance) `!_`(issubclass)
* loop @
* branch ?
* try % /% !%
* thread |
* comptime $

* join <> << >> ><
* reference &
    * pass by name instead of by value

compound literal types
* function <>:()
* object {:}

other functions
* load - import file

other builtin types
* iter - an iterator
* mat - a numeric matrix type
* type

traits, aka generics, aka interfaces
* ffi - foreign function interface
* itr - iterator
* cmp - comparable, well ordered?
* fun - callable. blk, uop or bop

# tables v0.2
expose sqlite as a language feature for persistence and querying
operations like loop, join and filter should have the same syntax
for sqlite based or in-memory types
zip / join
other builtin types
* tab - a sqlite table
* ⨝`u2a1d` new `ji` (join)
* ⟕`u27d5` new `j]` (left join)
* ⟖`u27d6` new `j[` (right join)
* ⟗`u27d7` new `jo` (outer join)

can this handle sqlite and pandas use case?

# I/O and concurrency v0.3
I/O should have chan semantics.
allow coprocesses which communicate exclusively through channels
sys module for calling external programs
what about audio/visual i/o as primitives in addition to files.

literal functions
* proc |

other types
* chan - a typed thread-safe queue that produces a value or blocks

# aliases v0.4
bidirectional updates between variables. reversible functions
literal function
* alias <->

# fstrings, regex, requests v0.5
implement fstrings as a syntax
[fstring](https://news.ycombinator.com/item?id=31457188)
add regex and http request libraries

# ecosystem v0.6
datetime
what's the mvp for an xorg/wayland-like graphics env

## ops
* casting - cast should be a complete function between all builtin types
* comparisons =≥≠≤><
* bitwise &(b-and) ¦(BB)(bit or)
* math * (mul) /(div) %(mod) -(inv/sub) +(add) ±(abs) 
* logical !(not) ∨(OR)(or) ∧(AN)(and) ×(\/)(xor) ¬(-,)(not)

## flow control
* line - simple expressions are evaluated in linear order
* func - λ and Λ cause a jump in memory
* chan - a chan read may block while waiting for a value
* proc - a thread may run in parallel
* case - a branch chooses one of several sections to run
* loop - a loop repeats a section
* try  - a handle exceptions and errors
* load - import a library, aka jump to a file
* ‖(||) a language thread (concurrent/parallel execution)
    * ¥(Ye) ⑂(2h) join/wait
    * read/write channel
* ⟂(u27C2) ⊥(T-) branch execution ≡(=3) Ϡ(P3) ?
    * default pair
* @(loop)∘(Ob) ↻(new Q>)
    * « (<<)continue
    * » (>>)break
* try catch... finally
* import
* loop
    * the only difference is that a map can happen in any order becaue it doesn't (shouldn't) have side effects
      while a for loop can make arbitrary changes to external values.
    * filter is the same, as long as we have the sentinel nil which cannot be in the output (repeat after me, nil is not a value).
    * where map is a function x -> y, reduce is a function x,y -> z
      we have separate function types for 1-adic and 2-adic functions
      so this is fine.
## iter
* ∘`Ob`/r map (with λ) or reduce (with Λ)
* ↕`UD`/R sort/rearrange
* ↔`<>`/f filter
* ‥`..`.. count/range/slice
* ∷`::`:: groupby
* ∝`0(`/@ cycle repeat sequence
* ∇`NB`/z zip
* ∆`DE`/Z zip longest
* ∃`TE`/E any
* ∀`FA`/A all
higher order functions
* map/reduce/filter
* groupby
* partial



## set
* ∋`-)` /k has key
* ⊇`_)` /s is subset
* ⊃`C)` /S is strict subset

can we do auto AOS↔SOA conversion
* make unused declarations a debug build warning and production build error
# tooling
## keyboard
take notes from the [bqn keyboard](https://mlochbaum.github.io/BQN/tutorial/expression.html#arithmetic)


* sequence of values

# types
* scalar - a single thing
* sum - this or that
* vector - this and that
* sequence - zero or more of this

# call types
* function application
* method application
* map application
* filter application
function and method application should be in the same order, but distinguished somehow

# VSO or SVO
data is the subject
function is the verb
object is the arguments

# adverbs
* . (dot) - this verb is a member of a namespace

# core types
scalar
* int
* float
* char

sequence
* seq - zero or more values
* list
* set
* `:` pair
* `{}` namespace (dict)
* string
* func
* enum
# core language constructs
* assignment/definition
* comparisons
* algebra
* boolean algebra
    * and, or, xor, not
* filter/map/reduce
* loops/repetition
* list/set/dict
* function/expressions
* class
# booleans
an expression is falsey if it produces no values, otherwise it is truthy
# filtermap
`~` is filtermap. The RHS is a function of one argument.
filtermap returns a flattened sequence from the sequences produced by its RHS.
'filter' is the special case where the RHS only produces zero or one value.
'map' is the special case where the RHS produces exactly one value.

# reduce
`$` is reduce. The RHS is a function of two arguments

## comparisons are special cases of filter
x > 3 produces the left value (which is x) if x is greater than 3, otherwise it produces no values.
the same holds for all 6 comparisons (= > < != !> !<). These are all filters.
## arithmetic is a special case of map
x + 3 produces the expected value `(1|2)+3 -> (4|5)`

# functions
`->` LHS is a sequence of names that are bound, RHS is either the produced sequence, or a namespace to evaluate.
`<-` acts as yield, `<<` as return

[expressions produce zero or more values](https://simon.peytonjones.org/assets/pdfs/haskell-exchange-22.pdf)
lazy evaluation?
```
x := 1
y := (x|2)

abs := (x: int): int -> (x !< 0 ? x : -x)
abs := (x: int): int -> {<- x !< 0 ? x : -x}
```
# ref
* [python builtins](https://docs.python.org/3/library/functions.html)
* [python itertools](https://docs.python.org/3/library/itertools.html)
* [bqn](https://mlochbaum.github.io/BQN/tutorial/expression.html)
* [elixir](https://learnxinyminutes.com/docs/elixir/)
* [syntax across languages](http://rigaux.org/language-study/syntax-across-languages.html)
