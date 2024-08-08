from base import *
import networkx as nx

from dataclasses import dataclass


class Graph(Evaluator):
    """
    a base graph optimizer and evaluator

    subclasses should define compile(ast) -> nx.Digraph
    Where each node is a function and each edge represents a dependency.
    Each function will be called a set of incoming edges and a set of outgoing edges.
    outgoing edges must be marked 'ok' if the computation should proceed in that direction.

    Nodes are eligible to run if they have no incoming edges, or if all incoming edges are 'ok'

    The order of node execution depends only on the edges.
    compile() may call optimize(G) to make use of general graph-level optimizations.
    """
    def __init__(self, ast:node|None=None):
        self.graph = None if ast is None else self.compile(ast)

    def __call__(self, ast:node|None=None, vis:Visualizer|None=None):
        if ast is None:
            if self.graph is None:
                raise ValueError("don't have any code to run")
            G = self.graph.copy()
        else:
            G = self.compile(ast)

        return self.run(G, vis)

    #@abc.abstractmethod
    def compile(self, ast:node) -> nx.DiGraph:
        """compile ast into a graph."""
        # TODO convert ast to graph here
        #   make sure to call self.optimize for optimization
        raise NotImplemented

    def optimize(self, G:nx.DiGraph):
        """Do graph level optimization."""
        # cull the graph to the subset needed to compute targets
        needed = set()
        for n in G.nodes(target=True):
            needed |= n.ancestors()
        G = nx.induced_subgraph(G, needed)
        if not nx.is_directed_acyclic_graph(G):
            raise CompileError('cycle detected in computation graph.')
        return G

    def clear(self):
        """clear and reset computation graph."""

    def run(self, G:nx.DiGraph, vis:Visualizer|None=None):
        """execute the computation graph."""
        G = G.copy()
        for n in nx.topological_sort(G):
            if vis:
                for e in G.in_edges(n):
                    G.edges[e]['color'] = vis.active
                G.nodes[n]['color'] = vis.active
                vis.add_frame(G)
                for e in G.in_edges(n):
                    G.edges[e]['color'] = vis.done
                G.nodes[n]['color'] = vis.done
                for t in G[n]:
                    G[n][t]['color'] = vis.ready
        if vis:
            vis.add_frame(G)


empty = object()

@dataclass
class Fermion:
    kind:str
    value:object=empty
    position:bool|None=None
    def unwrap(self):
        if self.position is None:
            raise EvalError(f"Tried to unwrap value that hasn't yet been determined")
        if not self.position:
            raise EvalError(f"Tried to unwrap value that wasn't produced.")
        return self.value

    def ok(self, value=empty):
        if self.position is not None:
            raise EvalError(f"Tried to set fermion value twice.")
        self.position = True
        self.value = value

    def nok(self):
        if self.position is not None:
            raise EvalError(f"Tried to set fermion value twice.")
        self.position = False

class Boson:
    """
    For convenience to wrap calls to normal python functions.
    Also as an example of how to handle effects
    """
    def __init__(self, func):
        self.func = func
    def __call__(self, incoming:tuple[Fermion,...], outgoing:tuple[Fermion, ...]):
        # TODO how to make sure these are in the right order?
        args = tuple(a.unwrap() for a in incoming)
        try:
            value = self.func(*args)
            for f in outgoing:
                if f.kind == 'value':
                    f.ok(value)
        except Exception as e:
            for f in outgoing:
                if f.kind == 'throw':
                    f.ok(e)
        for f in outgoing:
            if f.position is None:
                f.nok()




