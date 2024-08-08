# Quark

a minimal-ish set of semantics for use with treerat syntax

1. parse syntax -> ast
2. graph generation -> graph
    * name resolution
    * type & effect checking/inference
3. scheduling - dynamic

# terminology
sometimes it is useful to define 'new' words in order to discuss particular concepts. Rather than using actually new words, I'll be reusing words from the domain of particle physics to discuss the domain of programming. This is preferable because anyone with a passing familiarity with particle physics probably knows how to pronounce the words, there is already some existing structural relationship between the words, there are enough of them, and the physics domain is different enough from programming that there is no question which concept is being referred to.

* boson - a unit of computation represented by a node in a graph
    * gluon - foreign function
    * photon - a compiled thread of native computation
    * higgs - a computation of zero argumnts which encodes literal values
* fermion - a datum represented by a directed edge in a graph
# What are the semantics of a langauge
* the native types
* type system
* execution/computation strategy
* name resolution


# definitions
While it is intended that any syntax can be used to represent these semantics, we define the following syntax in order to properly discuss the semantics. The given syntax is by no means official, or even necessarily good.

* a single capitol letter like `T` usually stands in for any type. `list<T>` means a list of values with type T, or the generic type `list` parameterized by the type `T`
* `f:A->B->C` means a function named `f` that takes an argument of type `A` and `B`, returning a value of type `C`. The name may be omitted.
* `...` is a variable number of things. `...T` is one or more types

# concepts
* generic container types - list<int> is a list that can only contain ints
* property derived types - 
* arbitrary assertions on values by the type system
    * bounded numbers
* full language available at comptime, compiler available at runtime unless trimmed.
* implicit casts are functions `T->N` that are explicitly marked with the property `cast`
    * type inference may insert casts **anywhere** it is needed to match explicitly given types
    * ther
* function overloading
    * the tuple (function name, arg types, return type) must be unique.
    * furthermore all defined return types for a given name cannot cast to one another.
        * `f:A->B`, `f:A->C` and `cast<B,C>` cannot all exist, since it is ambiguous.

# native types
* nulltype - nulltype has a single value (null), which is never equal to anything, even itself. The check against the identity of null
* int - an integer
* float - a floating point number
* complex - a complex number, implemented as two floats
* type - the type of all types
* function - [closures](https://en.wikipedia.org/wiki/Closure_(computer_programming))
* string - a unicode (utf-8) string
* bytes - a sequence of bytes
* map<K,V> - a mapping of key-value pairs
* list<T> - a sequence of values
* matrix - an n-dimensional array of numbers

* either<...T> - a [sum type](https://en.wikipedia.org/wiki/Tagged_union)
    * converted to base type by pattern matching, which must cover all options
* tuple<...T> - a [product type](https://en.wikipedia.org/wiki/Product_type)

* bool - implemented as a bounded int[0,1]

# properties
Properties are used during [type inference](https://en.wikipedia.org/wiki/Type_inference).
Types can explicitly declare that they implement a property.
Properties may also implement a function `type -> bool`, to implicitly prove that types implement the interface, unless 
These properties are then used to derive types 
properties are flags that apply to types

* iterable<T> - produces a sequence of T
* pairs<K,V> - produces pairs of values K,V
* cast<T,N> - defines a function `T->N` which can be used to implicitly cast types
