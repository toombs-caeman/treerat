import subprocess
import tempfile
import copy

import graphviz
from itertools import count
from collections import defaultdict

import graph
import standard
import parser
import evaluator

class Digraph(graphviz.Digraph):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.frames = []
    def next_step(self, reset:bool|int=False):
        """add a new frame to the graph animation and optionally reset the graph to a previous frame"""
        reset = -int(reset)
        self.frames.append(copy.deepcopy(self))
        if reset:
            self.body = self.frames[reset-1].body
    def gif(self, outfile:str, delay=100):
        """create an animated gif"""
        filecount = len(self.frames) + 1
        #print(f'making {filecount} temp files')
        files = [tempfile.NamedTemporaryFile(suffix='.png') for _ in range(filecount)]
        for i, g in enumerate(self.frames):
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



def vis(data:parser.node|graph.graph|standard.Model|None, *args) -> Digraph:
    """Dispatch visualizations based on type of data to visualize."""
    match data:
        case parser.node():
            return vis_ast(data, *args)
        case standard.Model():
            return vis_model(data, *args)
        case None:
            print(f"a call to vis received None: {args!r}")
        case _:
            print(f"don't know how to visualize {type(data)}: {args!r}")
    return Digraph()

def vis_ast(ast:parser.node, source:str|None=None):
    dg = Digraph()
    id = map(str, count())
    def walk(ast, i):
        match ast:
            case parser.node():
                dg.node(i, label=ast.kind)
                for ia,(a, I) in enumerate(zip(ast, id)):
                    walk(a, I)
                    dg.edge(i, I, label=str(ia))
            case tuple():
                dg.node(i, label='()')
                for ia,(a, I) in enumerate(zip(ast, id)):
                    walk(a, I)
                    dg.edge(i, I, label=str(ia))
            case _:
                dg.node(i, label=repr(ast))
    walk(ast, next(id))
    if source:
        i = next(id)
        l:str = source.replace('\n', '\\l')
        if not l.endswith('\\l'):
            l += '\\l'
        dg.node(i, shape='box', label=l, labelloc='t')
    return dg

def vis_model(model:standard.Model, name='comp'):
    dg = Digraph(name, strict=True)
    # make all nodes with labels
    for h,b in model._bosons.items():
        op, *args = b
        dg.node(str(h), label=f"{op}({', '.join(map(repr, args))})" if all(isinstance(a, str) for a in args) else op)
    # map comp to predecessors
    G = graph.map(model._graph, str)
    rG = defaultdict(set)
    # make all edges
    for h, tails in G.items():
        for t in tails:
            dg.edge(t, h)
            rG[t].add(h)
    try:
        order = [str(hash(n)) for n in model.order]
    except graph.CycleError as ce:
        err = Digraph('error')
        err.attr(label='cycle detected', labelloc='t')
        for h, tails in ce.args[0].items():
            h = repr(h)
            err.node(h, label=h)
            for t in tails:
                t = repr(t)
                err.edge(t, h)
        err.render(outfile='error.png', format='png', cleanup=True)

        dg.next_step()
        for n in G:
            dg.node(n, color='red')
        return dg

    # highlight the order of execution
    WAIT  = 'black' # computation is not ready, black is the default color
    READY = 'blue'  # computation is ready to proceed
    ACTIVE= 'green' # computation is active during this step
    DONE  = 'gray'  # computation is complete
    for n in order:
        # mark current node as active
        for t in G[n]:
            dg.edge(t, n, color=ACTIVE)
        dg.node(n, color=ACTIVE)
        # transition to the next step
        dg.next_step()
        # mark the old node as done
        for h in rG[n]:
            dg.edge(n, h, color=READY)
        for t in G[n]:
            dg.edge(t, n, color=DONE)
        dg.node(n, color=DONE)
    return dg


if __name__=="__main__":
    import testlang
    
    ast = testlang.sample_ast
    vis(ast, testlang.sample).render(outfile='ast.png', cleanup=True, format='png')

    # name resolution / computation graph generation
    names = evaluator.namespace() # comp hashes, keyed by a name which currently refer to them
    model = standard.Model()
    total_orders = {}
    def x(n:parser.node):
        if not isinstance(n, parser.node):
            return n
        match n.kind:
            case 'start':
                for stmt in n:
                    x(stmt)
            # 'statements' don't need to return anything
            case 'Assign':
                name = n[0][0]
                val = n[1]
                # notice that this step fully eliminates names from the output
                names[name] = x(val)
            # 'expressions' return their computation
            case 'Scope':
                v = None
                with names:
                    for stmt in n:
                        v = x(stmt)
                return v
            case 'Var':
                return names[n[0]]
            case 'Print':
                last_print = total_orders.get('Print', None)
                expr = x(n[0])
                comp = ('Print', expr)
                dep = (expr,) if last_print is None else (comp[1], last_print)
                comp = model.node(comp, *dep)
                total_orders['Print'] = comp
                model.add_target(comp)

            case _:
                print(n.kind, n.children)
                comp:list[int|str] = [n.kind]
                deps = []
                for a in n:
                    if isinstance(a, str):
                        comp.append(a)
                    else:
                        a = model.node(x(a))
                        comp.append(a)
                        deps.append(a)
                return model.node(tuple(comp), *deps)
    x(ast)
    
    vis(model).gif('compute.gif')
