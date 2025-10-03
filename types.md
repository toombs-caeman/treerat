
value have types, names have traits.

1.  `E : T` In this case, both an expression E and a type T are given. Now, is E really a T? This scenario is known as type-checking.
2.  `E : ?` Here, only the expression is known. If there is a way to derive a type for E, then we have accomplished type inference.
3.  `? : T` The other way round. Given only a type, is there any expression for it or does the type have no values? Is there any example of a T? This is known as type inhabitation.
Its not clear to me if this can happen after graph generation, but I think it probably can. Fermions probably should record names as debug symbols
# process
1. collect names and whatever else must be typed, along with explicitly given trait information. (name resolution)
    * names don't necessarily have constant type, but explicitly given types or traits are propogated to each use.
    * literals like `1` are not given an real type, but given the `numeric` trait, with members `int`, `float`, etc.
2. propogate traits (type inference) until all conditions check
3. resolve traits into real types (type instantiation) or fail
4. resolve generic types for multiple dispatch
    * function lifting (implicit map) when?

It may be that type checking can be a separate phase from name resolution, as long as explicit trait information is propogated correctly.
If a name is given an explicit trait then what is the expectation? Should that name always resolve to the same real type or should that name only the trait invariant, and allow any type
# 
* Every name can be given a type. Fermions have a type.
* need ordered and unordered scope.
# ordered scope
* imperative code usually uses ordered scope, meaning that name resolution may depend on the order of assignments. However some statements can be declarative (forward declaration) and hold true for the lifetime of the names involved (aka, the lifetime of the enclosing scope).
# unordered scope
* type declarations are what come to mind, but can we allow arbitrary invariants to be asserted?
* consider an unordered scope `y = x * x; y = 2 - x`
    * can we solve the system of equations to assign values to x and y?
    * at least mutually restrict the values of x and y to form a bi-directional alias?


Could be implemented as a generic constraint solver???

# GIR
all value types and effects must be resolvable in order to construct the complete graph.
what can be explicitly assigned a type?
* effects?
    * raise exceptions

# How can we attempt to recover?
* adding implicit casts
* interfaces

# traits, second order types, 
Traits are assertions about types or values.
A value in type `T` implements all traits of `T` by definition.
In this way membership to a type can be considered a trait applied to values.
However traits are not types.

Types must provide a mechanism to instantiate values (even if the type is empty and has no values).
In contrast, traits only need to be able to compute membership.

During type instantiation each collection of traits is resolved to a real type that implements that collection of traits (or more).


# things which should maybe be expressable by the type system
* generic types
* Assign traits to type by fiat `tuple impl Iterable`
* Explicitly define the members of a type (Enum) `bool={0,1}`
* sum and product types `number={x∈int, x∈float}`, `pair=(int, int)`
* Restrict a type by applying arbitrary conditions to values. `N={x∈int|x>0}`
    * assign rules for what happens to the value when the assertions of a restricted type are violated (clamp, fail, mod).
    * [dependent types](https://en.wikipedia.org/wiki/Dependent_type) (I believe this a direct consequence of allowing product types and restriction by values)
* Derive traits from arbitrary properties of type `Iterable={T|iter[T]}`
    * meaning a type `T` implements the trait `Iterable` iff there is a function overload `iter` that matches `T`
* Define types as equivalent by defining an implicit cast between them (or in one direction only)
    * implicit casts may be inserted by type inference
* heuristic traits indicate expected latency of effects, size of inputs, hot path, include debug symbols, complexity class, etc.
    * provide hints to type instantiation and the scheduler

Other traits may be explicitly assigned to assert facts about behaviour that the language.

Other traits may assist with heuristics, like marking functions which may take a long time,
or network reads which may have high latency.

# generics, polymorphism, overloading, 
* [multiple dispatch](https://en.wikipedia.org/wiki/Multiple_dispatch)

# ref
* [set builder notation](https://en.wikipedia.org/wiki/Set-builder_notation#Sets_defined_by_a_predicate)
* language of [conjunctive queries](https://en.wikipedia.org/wiki/Conjunctive_query) for efficiency?
https://en.wikipedia.org/wiki/Effect_system
https://en.wikipedia.org/wiki/Type_inference
https://www.reddit.com/r/ProgrammingLanguages/comments/q8j0f1/implementing_traitsinterfacestypeclasses_in_a/
[scheme lexical scope](https://docs.scheme.org/schintro/schintro_53.html)
[typechecker zoo](https://sdiehl.github.io/typechecker-zoo/)
