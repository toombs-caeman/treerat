# type heirarchy
low-level types
* num - generic number
    * int
        * {i,u}{16,32,64}
        * {i,u}size
    * float
        * f{16,32,64}
* string - pythonic immutable strings
    * arr[char]
* iterable - generic iterable
    * array - immutable, uniform type
    * vector - 
* collection
    * set
    * dict
        * namespace
    * tuple - immutable, 
* ref - rustic pointer
    * raw pointer
* producer
    * function
        * FFI
    * coroutine
        * remote call
join python sql and apl in an unholy union
allow dense array syntax but encourage pythonic style
allow persistence and strong consistency guarantees by embedding a sqlite database

# orthogonal syntax
unify parts of programming languages that are typically similar but different syntax.

for..in, foreach, and map are closely related keywords across many different languages.
All use cases of these are served by the singular loop, aka '@'.
Loop also handles the need for while, do..while, reduce and filter.

Similarly, '?' handles the need for if, else, and case keywords

only use one quote style for strings

prefer expressions (and blocks) over statements

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

# semantics
values and expressions
* a value is a scalar (number string or a collection of values)
* an expression is not a value, but may produce a value (zero or one)
* names may be assigned to expressions or values
* there are three types of expressions which are not values: blocks, functions, operators
    * blocks take zero arguments
    * functions and blocks

# meta-syntax v0.0
define foreign function interface (ffi).
use unicode literal functions for meta-programming.
perhaps meta-language mechanics uses unicode characters,
while the more common language elements can use ascii symbols
methods for modifying the parsing grammar
use precedence climbing

before cementing syntax with any backward compatible processes, generate permutations of 'valid syntax'
and make sure they have clear semantics. All parsable expressions should have clear semantic meaning
(whether or not it is a useful construct, or valid code in this instance.

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
