import subprocess
import tempfile
import copy

import graphlib
import graphviz
from itertools import count
from collections import defaultdict

import parser


class Digraph(graphviz.Digraph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__previous = []
    def next_step(self, reset:bool|int=False):
        """add a new frame to the graph animation and optionally reset the graph to a previous frame"""
        reset = -int(reset)
        self.__previous.append(copy.deepcopy(self))
        if reset:
            self.body = self.__previous[reset-1].body
    def gif(self, outfile:str, delay=100):
        """create an animated gif"""
        filecount = len(self.__previous) + 1
        #print(f'making {filecount} temp files')
        files = [tempfile.NamedTemporaryFile(suffix='.png') for _ in range(filecount)]
        for i, g in enumerate(self.__previous):
            g.render(outfile=files[i].name, cleanup=True, format='png')
        self.render(outfile=files[-1].name, cleanup=True, format='png')
        cmd = ['magick']
        for file in files:
            cmd.extend(( '-delay', str(delay), file.name))
        cmd.append(outfile)
        #print(' '.join(cmd))
        subprocess.call(cmd)
        for f in files:
            f.close()

def comp_viz(comps:dict, effects=(), order=(), name='comp'):
    effects = tuple(map(str, effects))
    order = tuple(map(str, order))

    vis = Digraph(name, strict=True)
    # construct graph
    main = 'main'
    vis.node(main, label='Entrypoint')

    outgoing = defaultdict(list)
    incoming = defaultdict(list)
    def edge(tail, head, label=None):
        e = tail, head
        vis.edge(*e, label)
        outgoing[tail].append(e)
        incoming[head].append(e)

    for eidx, e in enumerate(effects):
        edge(e, main, str(eidx))
    for k,(op, *args) in comps.items():
        if all(isinstance(a, str) for a in args):
            vis.node(str(k), label=f"{op}({', '.join(map(repr, args))})")
        else:
            vis.node(str(k), label=op)
            for a in args:
                edge(str(a), str(k))
    vis.next_step()
    if not order:
        vis.node(main, color='red')
        return vis

    # highlight the order of execution
    WAIT  = 'black' # computation is not ready, black is the default color
    READY = 'blue'  # computation is ready to proceed
    ACTIVE= 'green' # computation is active during this step
    DONE  = 'gray'  # computation is complete
    # highlight computations in the order they are executed
    # hold the complete graph before resetting

    def done(n):
        for e in outgoing[n]:
            vis.edge(*e, color=READY)
        for e in incoming[n]:
            vis.edge(*e, color=DONE)
        vis.node(n, color=DONE)

    def active(n):
        for e in incoming[n]:
            vis.edge(*e, color=ACTIVE)
        vis.node(n, color=ACTIVE)

    for n in order:
        active(n)
        vis.next_step()
        done(n)
    vis.next_step()
    done(main)
    return vis


def ast_viz(ast):
    id = map(str, count())
    vis = Digraph()
    def walk(node):
        i = next(id)
        match node:
            case str():
                vis.node(i, label=repr(node))
            case list():
                t, *args = node
                vis.node(i, label=t)
                for ai, a in enumerate(args):
                    vis.edge(i, walk(a), label=str(ai))
        return i
    walk(ast)
    return vis

if __name__=="__main__":
    import testlang
    
    ast = testlang.sample_ast
    #print(ast)
    if ast is None:
        print('parse failed')
        quit()
    # visualize ast
    ast_viz(ast).render(outfile='ast.png', cleanup=True, format='png') #, view=True)

    # name resolution / computation graph generation
    comps = {} # units of computation, keyed by their hash
    names = {} # comp hashes, keyed by a name which currently refer to them
    order = defaultdict(set) # for each comp hash, keep a set of preceeding comp hashes (for topological sort)
    effects = [] # a sequence of comp hashes with stateful effects (and which therefore must be fully ordered)
    def add_comp(comp):
        h = hash(comp)
        comps[h] = comp
        # depends on any arguments to the comp
        order[h] |= set(c for c in comp if isinstance(c, int))
        return h
    def add_effect(comp):
        h = add_comp(comp)
        if effects:
            # ensure that effectful computation has unambiguous ordering
            order[h].add(effects[-1])
        effects.append(h)
        return h
    def x(expr):
        match expr:
            # 'statements' don't need to return anything
            case ['Entrypoint', *stmts]:
                for s in stmts:
                    x(s)
            case ['Assign', ['Var', name], val]:
                # notice that this step fully eliminates names from the output
                names[name] = x(val)
            case ['Print', expr]:
                add_effect(('print', x(expr)))
            # 'expressions' return their computation
            case ['Var', name]:
                if name not in names:
                    raise NameError(name)
                return names[name]
            case ['Float', lit]:
                return add_comp(('float', lit))
            case ['Int', lit]:
                return add_comp(('int', lit))
            case [op, *args]:
                return add_comp((op, *(x(a) for a in args)))
    x(ast)
    # determine computation order
    # TODO rather than rely on graphlib, prioritize nodes by effects.
    #       the next effect should always be executed in the minimum number of steps
    try:
        order = list(graphlib.TopologicalSorter(order).static_order())
    except graphlib.CycleError:
        order = []

    # visualize computation
    comp_viz(comps, effects, order).gif('compute.gif')
