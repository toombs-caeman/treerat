start to consider type systems.

1.  E : T? In this case, both an expression E and a type T are given. Now, is E really a T? This scenario is known as type-checking.
2.  E : _? Here, only the expression is known. If there is a way to derive a type for E, then we have accomplished type inference.
3.  _ : T? The other way round. Given only a type, is there any expression for it or does the type have no values? Is there any example of a T? This is known as type inhabitation.

Could be implemented as a generic constraint solver???

what can be explicitly assigned a type?
* effects?
    * raise exceptions
    * 

How can we attempt to recover?
* adding implicit casts
* interfaces

Constraint/property based type definition. Type instantiation based on explicitly assigned traits

https://en.wikipedia.org/wiki/Type_inference
https://www.reddit.com/r/ProgrammingLanguages/comments/q8j0f1/implementing_traitsinterfacestypeclasses_in_a/
