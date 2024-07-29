# implementation specific compiler optimizations
a discussion of potential optimizations in order to implement the given semantics

* spatial & temporal locality

# Parsing
## ast type
```python
@dataclass
class Node:
    next: uint64 # index into source of the next character to consume
    kind: Enum  # the ast type of this node
    children: tuple[Node, ...] | str
```
a tree of Nodes, with string terminals.

Use [immediate objects](https://bernsteinbear.com/blog/scrapscript-tricks/#immediate-objects)?
* Most terminals are short ascii strings.
* Most node kinds have a small & fixed number of children. It may be productive to represent small subtrees as immediate objects as well.

Since packrat parsing is used, bad locality is expected. However, it may not be productive to re-pack the ast because it will usually be either immediately discarded (if not in final ast) or walked once to produce a particle graph then discarded.

Packrat parsing will produce the final ast in roughly depth first order (temporally). When the particle graph is constructed, it reads the tree in [post-order](https://en.wikipedia.org/wiki/Tree_traversal#Post-order,_LRN). Can use prefetch instructions?

## packrat cache
The cache is a mapping `(func, text) -> ast` of pure functions + arguments to return values. It is essentially the same as a particle graph.


# compiling
* bosons that consume no effects can be safely evaluated at compile time.
* bosons that produce no effects can be culled.

# photons
a subgraph of bosons may be densly connected internally, but sparsely connected externally.
It may be possible to replace the subgraph with a single boson (a photon), preserving its connecting edges.
However, since a photon (like any boson) produces all of its effects in a single scheduling step, this can (I think) create ordering problems in the larger subgraph.

It is expected that photons are faster (lightspeed, even) because:
* Scheduling within the photon only needs to consider the internal subgraph.
    * photons can bypass runtime scheduling by pre-ordering (effectively bytecode?).
    * fermions that aren't emitted are temporally local.
* photons can be made very cache friendly by, among other things, packing incoming fermions, and sizing photons according to expected internal memory usage and available cache size.

Photons may not be desirable in cases where:
* further graph rewriting is available (probably shouldn't nested photons)

# scheduling
While bosons may be executed in any topological order, some orders are (probably) better than others.
* for latency, schedule bosons necessary for the first effect first. This kind of sceduling may need to be dynamic (runtime). It may help to know the expected latency of effect types.
* consider temporal locality of fermions

## fermion-boson graph
representation is important
