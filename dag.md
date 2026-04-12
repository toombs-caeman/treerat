NOTE: so it turns out that this great original idea I had is called 'sea of nodes', and has been written about longer than I've been alive. Figures.

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

# Code is a DAG (abstract semantic graph ASG)
consider "source code" to be a description of a directed acyclic graph (DAG) of computation where edges are immutable values (even if they appear to change) and nodes are pure functions (even if they don't look pure in source).
Incoming edges are the arguments of that function (node), and outgoing edges are values produced by that function.
Functions "produce" values when they either return values, mutate values, raise exceptions or otherwise produce effects.
Looping constructs (for, while) appear to be cycles at first glance, but in fact this illusion is a convenient trick of name resolution. Loops are equivalent to either maps (one or many related values fanned out to copies of the same function or code block) or reductions (a chain of repeated applications to the original value).

A node is ready for execution after all of the incoming edges have been produced.
Edges are potential, and may not be produced during the execution of a node.

This graph is fractal. Functions may themselves be considered DAGs. Let us consider a special SOURCE node that "produces" all of the arguments of a function, and a special SINK that "consumes" the function's products.

Computation which produces no effect may as well not have happened. Nodes with no outgoing edges can be culled (other than the special SINK).

When considering the whole program, what are SOURCE and SINK? The program's SOURCE node produces all literal values which were embedded in the executable. SOURCE also provides user input and values from external programs. SINK consumes any external effect produced by the program, printing to the terminal for example. The implementation of SOURCE and SINK in this context must be impure primitive functions.

Naturally a function's SOURCE and SINK nodes don't need to actually exist in the complete graph, as they just serve as pass-throughs for collections of values. The barrier of a function definition need not exist in the DAG.

# What about names?
Names (which may be called variables) refer to values (which may be first class functions, or types, exceptions, etc.).
Where do names appear in our model of code-as-a-DAG? That's the neat part:They don't.

Names are useful to humans who read code, and to refer to values which are consumed in multiple places. However, the DAG is not intended for human comprehension, and we need to be more precise about "referring to values". The value to which a name (within a given scope) refers may change between de-references always, never, or sometimes.

If the value always changes between uses, its name can be resolved to edge-values independantly, as if it were multiple separate names.

If the value never changes, the name may be modelled as an "edge" with a single source and multiple destinations. The fact that the value doesn't change may be enforced by the language through "const" or by default (imutability in rust), but it may also just be a quirk of usage. The point is that, in this case, no computation can potentially change the value between usages.

There are two reasons why a value might "sometimes" change. If a value changes over time due to external circumstance it should be modeled as a series of SOURCE nodes that always modify the value. So finally, how do we model a value that changes conditional to other internal values? (but actually how do you sync

Finally, how do we model conditional change?

Conditional flow constructs can in general be modeled as a node which, when ready, produces only one of two or more potential values. These "ready" values are not usually used by the destination nodes, but are required for those nodes to be ready like any other edge. Therefore, only one "branch" will ever be ready. A typical "if" statement would produce two such values, while a "case" statement might have many.

However, this creates a problem. Consider the following python.
```python
x = 0           # block 0
...
if x:           # conditional
    x = x + 1   # block 1
    ...
else:
    x = x + 2   # block 2

x = x + 3       # block 3
```
Block 0 produces a value used in the conditional so an edge points from block 0 to conditional. The conditional produces a ready value for either block 1 or 2, but not both. Then block 1 and 2 both have an edge pointing to block 3. So block 3 needs block 1 and 2 to both produce a value in order to be ready but they never will!
We need a third kind of special node ANY, which is ready when all of its incoming ready values are produced and any one of its other incoming edges are ready. ANY produces the one value it consumes.

This is quite a lot of effort, but garuanteeing that only one branch can be taken with the conditional node, and joining each branch with the ANY node, effectively encapsulates the conditionality of the value.

And how does this affect name resolution?
The name before and after the condition can be resolved independantly, like in the "always changes" case. Within the conditional, the value either changes and is passed to an ANY, or is passed directly to ANY. Either way after the conditional the name resolves to the edge produced by ANY.

# More than just a DAG
So that's a bit more than just a run of the mill directed acyclic graph. Let's recap.

* Edges
    * have one tail and one or more head
    * are either ready or not ready
    * two types
        * ordering edges - represents readiness only
        * value edges - represents an immutable value if ready
* Nodes
    * represents a function (really the application of a pure function, when functions are a value)
    * arguments to the function are represented as incoming edges
    * effects of the function (including return value) are represented as outgoing edges
    * states: not ready, ready to execute, done executing
    * four types
        * normal - ready when all incoming edges are ready
        * ANY - ready when all incoming ordering edges are ready and the first value edge is ready
        * SOURCE - readiness depends on factors external to the DAG. may not become "unready" after being "ready"
        * SINK - not culled if they don't have outgoing edges, since effects may be external.

# More than just a DAG
So that's a bit more than just a run of the mill directed acyclic graph. Let's recap.

* Edges
    * represents the potential for an immutable value (or effect) to be produced
    * each tail represents a location which may produce this value. There is usually one tail, unless joining branches.
    * each head represents a location where the value is referenced by further computation.
    * readiness flag
        * becomes ready when any tail node produces this value. All other tail nodes immediately lose this edge as a SINK and may be de-scheduled
        * since the value is immutable, becoming ready is one-way.
        * it is an error to evaluate any head node when the edge is not ready.

* Nodes
    * represents a function (really the application of a pure function, when functions are a value)
    * arguments to the function are represented as incoming edges
    * effects of the function (including return value) are represented as outgoing edges
    * states: not ready, ready to execute, done executing
    * four types
        * normal - ready when all incoming edges are ready
        * ANY - ready when all incoming ordering edges are ready and the first value edge is ready
        * SOURCE - readiness depends on factors external to the DAG. may not become "unready" after being "ready"
        * SINK - not culled if they don't have outgoing edges, since effects may be external.

* (potentially) infinite loops need to have some way to collapse the graph in order to make the graph reasonably representable, even for turing complete programs.
    * maybe encapsulating subgraphs within a stateful REPEAT node so that the subgraph can be dynamically instantiated.

# Why
This framing creates a natural way to talk about (and code) optimization.
* Trimming dead code becomes finding nodes without outgoing edges and culling them.
* re-ordering statements for better cache performance? We already have a graph of actual value dependencies that abstracts away the order it happened to be written in.
    * since connected subgraphs can be substituted for nodes with the same interface, cache-performant subgraphs can be compiled to a hotpath, and substituted in. Values produced only for this hotpath can be co-located in memory. (superstrings?)
* who cares if the value was mutated, or if a new value was returned. Let the compiler figure out which is more efficient. What happens to the actual memory shouldn't be the programmers concern. We still have to care about reference semantics though
* You can precompute values at compile time that don't depend on external SOURCE nodes.
* is there a performance difference between `list(map(str,x))`, `[str(v) for v in x]` or `for v in x:out.append(str(v))`? Why. The DAG is the same. There's no reason that optimization should stop at function boundaries. If your codebase is so huge that compiler performance is a problem, GPU accelerated DAGs anyone? I'm sure the crypto-bros have been working on it.
* any connected subgraph is equivalent to any other node or subgraph with equivalent incoming and outgoing edges. This gives a poweful way to discuss re-writing optimizations

It enables some wild features
* lazy evaluation? start at the SINK nodes and work backwards to find what needs doing.
* what if you have multiple algorithms to implement the same result (like multiple implentations of sort)? Just call them all and take the value of the fastest one with an ANY node.
* as long as every SOURCE, SINK and primitive function is typed, you can do static type checking, even if no user defined function or variable declares type.
* SOURCE and SINK nodes provide a natural place to handle security concerns, platform specific cruft, etc.
* automatic parallelization of code that's well suited to it. Look for [strongly connected subgraphs](https://stats.stackexchange.com/questions/368433/how-to-find-strongly-connected-subgraphs-in-a-graph) in the DAG.
* I haven't worked out exactly how yet, but I believe you can represent threads and synchronization primitives in the DAG as well. Deadlocking probably shows up as a cycle, and race conditions as ambiguously orderable SOURCE and SINK nodes.
    * autothreading maybe possible?
* if SINK nodes are annotated with priority, then nodes can be dynamically scheduled in order to minimize latency for that effect. For example, setting a user visible SINK

* What if SOURCE and SINK had a concept of latency and locality for their interactions with the outside world? The compiler could allocate computation across network boundaries depending on whether it is faster to crunch the numbers here and send it over the wire, or to send the data and crunch it there. If you have a sharded database and highly parallel code, the compiler could move code to the data transparently.
    * this 'automatic' is a bit rough, since you need a way to safely and transparently send data over the wire, and be aware of changing network topology and latency.

# threading
1. for loops are broken into map or reduce by functional programmers
    * maps: computation is not affected by order (unordered)
    * reductions: computation **is** affected by order (ordered)
    * special case: modifying loop var: still a reduction
    * special case: sum: reduction because order affects intermediate steps, but map because the function being applied is associative so the final result is unaffected by order. 
2. for loops are an efficient representation of maps, but not always an efficient implementation
    * maps can be threaded assuming that the computation is signifcant enough to cover the overhead of doing so.
3. In most languages, programmers must decide when and where to thread
    * to gain speed, the programmer must be aware explicitly of performance characteristics of functions and threads
    * to do so correctly, must be aware of data and effect dependency (especially difficult for languages with mutation)
    * often, must hard-code number of available threads, or use thread pools
    * small changes to the single threaded code can result in very different code for efficient threading.
        * in effect, explicit threads are inexpressive

Formula for (estimated) speedup, aka time saved by threading a map rather than single threading:
```
(function cost:F) * (# iterations:I) = (function cost:F + per thread overhead:O) * (# iterations: I) / (# threads: T) + speedup:S
S = FI - I(F+O)/T
S = I(FT-F-O)/T
S = I(F(T-1)-O)/T
```

under GIR, all bosons have a concept of (estimated) cost, and all pairs are unordered unless there is a fermion path between them. This means that the compiler both has ability to implicitly thread code and can use the speed up estimation as a heuristic to probabilistically maximize speed.

`future` and `sync` primitives to allow treating superpositions as values. `sync` unwraps the superposition and either produces a value or blocks. If the fermion becomes false then the thread can be culled (since it will never be able to go forward).
Really all values are futures, but the primitives allow syncing to futures before they are defined (in lexical order). If doing so creates a cycle, then that is detected at sync.

# TODO
* rewrite to better define bosons/fermions
* associative operators can have undirected/bidirectional fermions?
* applicable graph algorithms?
    * bridge detection, coloring - potential threading interfaces?
        * https://en.wikipedia.org/wiki/Spectral_clustering
        * LOBPCG
    * flow max - max/average throughput of a subgraph (useful for threading, estimating runtime for finite programs?)
* look at BEAM languages (erlang, gleam) for concurrency primitives
* network latency estimation for source nodes?
* the number of outgoing edges from subgraph is nx.volume
* nx.greedy_modularity_communities for generating sparsly connected subgraphs?
* [end-to-end graph-level optimizing compiler](https://arxiv.org/abs/1802.04799)
* [implicit threads](https://w3.cs.jmu.edu/kirkpams/OpenCSF/Books/csf/html/ImplicitThreads.html)
* [graph (ADT)](https://en.wikipedia.org/wiki/Graph_%28abstract_data_type%29#Representations)

# sea of nodes
* great talk [Parsing without ASTs and Optimizing with Sea of Nodes](https://www.youtube.com/watch?v=NxiKlnUtyio)
* [sea of nodes tutorial](https://github.com/SeaOfNodes)
* [sea of nodes](https://en.wikipedia.org/wiki/Sea_of_nodes)
* global code motion
* branching is handled in the graph using 'projections', 'regions' and 'phi'
