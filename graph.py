"""
Helper functions for working with directed graph structures.

basically graphlib, but I want to be able to "finalize" nodes to say
that they are ready to proceed even if the graph as a whole can still receive new nodes

Rather than disallowing changes to the graph after G.prepare(),
disallow adding predecessors to nodes after G.finalize(node)
"""
__all__ = ['graph', 'sort', 'map', 'CycleError']
from collections import defaultdict
from graphlib import CycleError

type graph[T] = dict[T,set[T]]

from typing import Callable
def map[A,B](G:graph[A], f:Callable[[A],B]) -> graph[B]:
    return {f(k):{f(n) for n in v} for k,v in G.items()}


def sort[N](G:graph[N], key = ...) -> tuple[N]:
    """
    Returns a topological sorting of nodes or raises CycleError.

    If a key is given, then sort by key whenever multiple nodes are ready.
    """
    G = defaultdict(set, G)
    # make sure that all nodes are accounted for in the keys of G
    # even those that don't have dependencies
    pending = set()
    for v in G.values():
        pending.union(v)
    for n in pending - G.keys():
        G[n] = set()
    out = [] # return value
    if key is ...:
        # ready nodes are pending nodes with no dependencies
        # we can process ready nodes in batches since we haven't specified an order
        while (ready:={n for n,p in G.items() if not p}):
            for n in ready:
                out.append(n)
                del G[n]
            for v in G.values():
                v -= ready
    else: # sort ready nodes by priority
        heap = [n for n,p in G.items() if not p]
        for n in heap:
            del G[n]
        heapify(heap, key=key)
        #print(len(G), 'keys', list(G))
        while heap:
            #print(len(heap), 'heap', heap)
            n = heappop(heap)
            out.append(n)
            ready = []
            for k,v in G.items():
                if n in v:
                    v.remove(n)
                if not v:
                    ready.append(k)
            for k in ready:
                del G[k]
                heappush(heap, k, key=key)
    if G:
        raise CycleError(G)
    return tuple(out)

# These bits are mostly copied from heapq, but heapq doesn't properly expose sorting by key (probably for efficiency)

def heapify(x, key=...):
    """Transform list into a heap, in-place, in O(len(x)) time."""
    n = len(x)
    # Transform bottom-up.  The largest index there's any point to looking at
    # is the largest with a child index in-range, so must have 2*i + 1 < n,
    # or i < (n-1)/2.  If n is even = 2*j, this is (2*j-1)/2 = j-1/2 so
    # j-1 is the largest, which is n//2 - 1.  If n is odd = 2*j+1, this is
    # (2*j+1-1)/2 = j so j-1 is the largest, and that's again n//2-1.
    for i in reversed(range(n//2)):
        _siftup(x, i, key=key)

def heappop(heap, key=...):
    """Pop the smallest item off the heap, maintaining the heap invariant."""
    lastelt = heap.pop()    # raises appropriate IndexError if heap is empty
    if heap:
        returnitem = heap[0]
        heap[0] = lastelt
        _siftup(heap, 0, key=key)
        return returnitem
    return lastelt

def heappush(heap, item, key=...):
    """Push item onto heap, maintaining the heap invariant."""
    heap.append(item)
    _siftdown(heap, 0, len(heap)-1, key=key)

def _siftup(heap, pos, key):
    if key is ...:
        key = lambda x:x
    endpos = len(heap)
    startpos = pos
    newitem = heap[pos]
    # Bubble up the smaller child until hitting a leaf.
    childpos = 2*pos + 1    # leftmost child position
    while childpos < endpos:
        # Set childpos to index of smaller child.
        rightpos = childpos + 1
        if rightpos < endpos and not key(heap[childpos]) < key(heap[rightpos]):
            childpos = rightpos
        # Move the smaller child up.
        heap[pos] = heap[childpos]
        pos = childpos
        childpos = 2*pos + 1
    # The leaf at pos is empty now.  Put newitem there, and bubble it up
    # to its final resting place (by sifting its parents down).
    heap[pos] = newitem
    _siftdown(heap, startpos, pos, key=key)


def _siftdown(heap, startpos, pos, key):
    if key is ...:
        key = lambda x:x
    newitem = heap[pos]
    # Follow the path to the root, moving parents down until finding a place
    # newitem fits.
    while pos > startpos:
        parentpos = (pos - 1) >> 1
        parent = heap[parentpos]
        if key(newitem) < key(parent):
            heap[pos] = parent
            pos = parentpos
            continue
        break
    heap[pos] = newitem

