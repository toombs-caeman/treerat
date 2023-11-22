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
