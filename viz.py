import subprocess
import tempfile
import copy

import graphviz
from itertools import count
from collections import defaultdict

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

import graph
def comp_viz(model:'standard.Model', name='comp'):
    vis = Digraph(name, strict=True)
    # make all nodes with labels
    for h,b in model._bosons.items():
        op, *args = b
        vis.node(str(h), label=f"{op}({', '.join(map(repr, args))})" if all(isinstance(a, str) for a in args) else op)
    # map comp to predecessors
    G = graph.map(model._graph, str)
    rG = defaultdict(set)
    # make all edges
    for h, tails in G.items():
        for t in tails:
            vis.edge(t, h)
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

        vis.next_step()
        for n in G:
            vis.node(n, color='red')
        return vis

    # highlight the order of execution
    WAIT  = 'black' # computation is not ready, black is the default color
    READY = 'blue'  # computation is ready to proceed
    ACTIVE= 'green' # computation is active during this step
    DONE  = 'gray'  # computation is complete
    for n in order:
        # mark current node as active
        for t in G[n]:
            vis.edge(t, n, color=ACTIVE)
        vis.node(n, color=ACTIVE)
        # transition to the next step
        vis.next_step()
        # mark the old node as done
        for h in rG[n]:
            vis.edge(n, h, color=READY)
        for t in G[n]:
            vis.edge(t, n, color=DONE)
        vis.node(n, color=DONE)
    return vis


def ast_viz(ast, source:str|None=None):
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
    main = walk(ast)
    if source:
        i = next(id)
        l:str = source.replace('\n', '\\l')
        if not l.endswith('\\l'):
            l += '\\l'
        vis.node(i, shape='box', label=l, labelloc='t')
        vis.edge(i, main, label='parse')

    return vis

class namespace:
    def __init__(self, nro:list[dict]|None=None):
        self.__nro = nro or [{}]

    def __getitem__(self, key):
        return self.__get(key, slice(None))

    @property
    def global_(self):
        return self.__nro[0]

    def __get(self, key, sl:slice):
        for ns in reversed(self.__nro[sl]):
            if key in ns:
                return ns[key]
        raise NameError(key)

    def __setitem__(self, key, value):
        self.__nro[-1][key] = value

    def __enter__(self):
        self.__nro.append({})
        return self

    def __exit__(self, *_):
        return self.__nro.pop()

if __name__=="__main__":
    import testlang
    
    ast = testlang.sample_ast
    ast_viz(ast, testlang.sample).render(outfile='ast.png', cleanup=True, format='png')

    # name resolution / computation graph generation
    names = namespace() # comp hashes, keyed by a name which currently refer to them
    import standard
    model = standard.Model()
    total_orders = {}
    def x(expr):
        match expr:
            case ['Entrypoint', *stmts]:
                for stmt in stmts:
                    x(stmt)
            # 'statements' don't need to return anything
            case ['Assign', ['Var', name], val]:
                # notice that this step fully eliminates names from the output
                names[name] = x(val)
            # 'expressions' return their computation
            case ['Scope', *stmts]:
                v = None
                with names:
                    for stmt in stmts:
                        v = x(stmt)
                return v
            case ['Var', name]:
                return names[name]
            case ['Print', expr]:
                last_print = total_orders.get('Print', None)
                expr = x(expr)
                comp = ('Print', expr)
                dep = (expr,) if last_print is None else (comp[1], last_print)
                comp = model.node(comp, *dep)
                total_orders['Print'] = comp
                model.add_target(comp)

            case [op, *args]:
                comp = [op]
                deps = []
                for a in args:
                    if isinstance(a, str):
                        comp.append(a)
                    else:
                        a = model.node(x(a))
                        comp.append(a)
                        deps.append(a)
                return model.node(tuple(comp), *deps)
            case str():
                return expr
    x(ast)
    
    comp_viz(model).gif('compute.gif')
