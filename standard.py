from functools import cached_property, cache
from collections import defaultdict
import graph

class UnkownBoson(Exception):
    """The Model contains an id (hash) of an unknown boson."""

class Model[boson]:
    """
    A directed graph of computation.

    Model represents function application as nodes and the results of functions as edges.

    Model.order is a topological ordering of targets and their dependencies.
    It prioritizes reaching each target in turn in the fewest steps.
    The purpose of this is to (ideally) minimize latency.
    Model.order will not traverse nodes which do not lead to any target.

    TODO
    * dynamic ordering like graphlib
    * repl? probably not, use a different evaluator
    * densly connected subgraph algorithm?
    * multiple dispatch in the context of name resolution?
    * loops - inductive proofs of cycle correctness?
    * types and casts
    """
    def __init__(self):
        # track nodes internally by their hash (int)
        self._bosons: dict[int, boson] = {}
        self._graph: graph.graph[int] = defaultdict(set)
        self._targets: set[int] = set()

    def cache_clear(self):
        """clear cached functions and properties."""
        for attr in ('order', 'targets'):
            attr = f'_{type(self)}__{attr}'
            if hasattr(self, attr):
                delattr(self, attr)
        self.__subgraph.cache_clear()

    def __getitem__(self, key:int):
        return self._bosons[key]

    @property
    def bosons(self):
        return self._bosons.values()

    def complete(self):
        """True if all bosons in graph are defined."""
        return all(k in self._bosons for k in self._graph)

    @property
    def graph(self) -> graph.graph[boson]:
        if not self.complete():
            raise UnkownBoson
        return graph.map(self._graph, self._bosons.__getitem__)

    def subgraph(self, target:boson|int) -> set[boson]:
        """Return the set of transitive dependencies of the given target node."""
        if not self.complete():
            raise UnkownBoson
        return {self._bosons[k] for k in self.__subgraph(self.__node(target))}
    @cache
    def __subgraph(self, target:int) -> set[int]:
        # It is necessary to track which nodes we've already seen to avoid cycles.
        # However, it is undesirable to differentiate cache entries by anything other than target.
        toplevel = not hasattr(self, '_subgraph_seen')
        if toplevel:
            self._subgraph_seen = set()
        else: # we've been called recursively
            if target in self._subgraph_seen:
                raise graph.CycleError
        self._subgraph_seen.add(target)

        all = {target}
        for t in self._graph[target]:
            all |= self.__subgraph(t)

        if toplevel:
            del self._subgraph_seen
        return all

    def add_target(self, *targets):
        new = {self.__node(t) for t in targets}
        self._targets |= new
        self.cache_clear()

    @property
    def targets(self):
        if not self.complete():
            raise UnkownBoson
        return tuple(self._bosons[k] for k in self.__targets)

    @cached_property
    def __targets(self) -> tuple[int]:
        # collect the graph of just targets
        tg = {t:self.__subgraph(t) & self._targets - {t} for t in self._targets}
        return tuple(graph.sort(tg))

    @property
    def order(self) -> tuple[boson]:
        if not self.complete():
            raise UnkownBoson
        return tuple(self._bosons[k] for k in self.__order)

    @cached_property
    def __order(self) -> tuple[int]:
        # map target subgraphs to priority
        tprio = {frozenset(self.__subgraph(t)):i for i,t in enumerate(self.__targets)}
        # map bosons to minimum target priority (the first target which requires that boson)
        # exclude bosons that aren't in any target subgraph
        bprio = {
                b:prio
                for b in self._bosons
                if (prio:=min((t for t in tprio if b in t), default=None)) is not None}
        # mask _graph to just selected bosons
        G = {k:self._graph[k].intersection(bprio) for k in bprio}
        return graph.sort(G, key=bprio.get)

    def node(self, node:boson|int, *predecessors:boson|int):
        self.cache_clear()
        return self.__edge(self.__node(node), *map(self.__node, predecessors))

    def __node(self, node:boson|int) -> int:
        if isinstance(node, int):
            return node
        h = hash(node)
        self._bosons[h] = node
        return h

    def __edge(self, node:int, *predecessors:int):
        self._graph[node] |= set(predecessors)
        return node



