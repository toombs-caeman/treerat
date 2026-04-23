"""
a datastructure representing a directed graph, to allow graph rewriting operations

# patch graph rewriting aka PBPO+
* need multigraph with labeled edges
    * labels form a lattice
* edge labels can encode type?
* a target is a graph of MatchNodes
    * MatchNode.match(Node) -> bool:
* a match is a mapping of all nodes and edges in the input graph to the target

# TODO
* visualize with pygraphiz

* libraries do this
    * egglog https://egglog-python.readthedocs.io/latest/explanation/2023_07_presentation.html
        * python bindings for rust library

# ref
    [PBPO+](https://www.youtube.com/watch?v=yajQ6gkFEHY)
    [egg](https://docs.rs/egg/latest/egg/tutorials/_01_background/index.html)
"""
from dataclasses import dataclass
from typing import Callable, NamedTuple, Self
# TODO patch graph rewriting
type halflink[T] = set[Node[T]]
class Node[T]:
    __slots__ = 'data', 'down', 'up'
    def __init__(self, data: T, down: halflink[T]|None = None, up: halflink[T]|None = None):
        self.data = data
        self.down:halflink[T] = set()
        self.up:halflink[T] = set()
        if down:
            self.dupdate(down)
        if up:
            self.uupdate(up)
    def validate(self):
        # all bidirectional links are maintained
        assert all(self in u.down for u in self.up)
        assert all(self in d.up for d in self.down)
    def clear(self):
        self.uclear()
        self.dclear()
    def uclear(self):
        for u in self.up:
            u.down.remove(self)
        self.up.clear()
    def dclear(self):
        for d in self.down:
            d.up.remove(self)
        self.down.clear()
    def uadd(self, other:Self):
        other.down.add(other)
        self.up.add(self)
    def uremove(self, other:Self):
        other.down.remove(other)
        self.up.remove(self)
    def uupdate(self, other:halflink[T]):
        self.up.update(other)
        for o in other:
            o.down.add(self)
    def dupdate(self, other:halflink[T]):
        self.down.update(other)
        for o in other:
            o.up.add(self)
    def dadd(self, other:Self):
        other.up.add(self)
        self.down.add(other)
    def dremove(self, other:Self):
        other.up.remove(self)
        self.down.remove(other)
    def unify(self, *others:'Node[T]', select=(lambda d, *_:d)):
        self.uupdate(*(o.up for o in others))
        self.dupdate(*(o.down for o in others))
        self.data = select(self.data, *(o.data for o in others))
        for o in others:
            o.clear()
    __lshift__ = uadd
    __rshift__ = dadd

class Graph:
    terms: set[Node]
    labels: dict[str, Node]

@dataclass
class Transform:
    pass


type match = Callable[[Graph], ]
type rewrite = Callable[[Graph, Node], None]

@dataclass
class GraphRewriter:
    transforms: list[Callable]
    def __call__(self, f):
        pass
