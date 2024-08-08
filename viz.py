import subprocess
import tempfile
import random
from itertools import count
import pygraphviz as gz
import networkx as nx

import parser
from base import *

type vis_enabled = gz.AGraph|nx.DiGraph|node|None
def normalize(__o:vis_enabled) -> gz.AGraph:
    # normalize data to gz.AGraph
    match __o:
        case gz.AGraph():
            return __o.copy()
        case nx.DiGraph():
            return nx.nx_agraph.to_agraph(__o)
        case node():
            G = gz.AGraph(directed=True)
            def walk(n):
                lits = []
                for i,a in enumerate(n):
                    if isinstance(a, node):
                        walk(a)
                        G.add_edge(n, a, label=str(i))
                    else:
                        lits.append(repr(a))

                label = f"{n.kind}({', '.join(lits)})" if lits else n.kind
                G.add_node(n, label=label)
            walk(__o)
            return G
        case None:
            return gz.AGraph(directed=True)
        case _:
            raise ValueError(type(__o), __o)

class Vis(Visualizer):
    def __init__(self, data:vis_enabled=None):
        self.frames = []
        data = normalize(data)
        if data:
            self.frames.append(data)
    @classmethod
    def from_eval(cls, evil:Evaluator, ast:node):
        vis = cls()
        try:
            evil(ast, vis=vis)
        except EvalError as e:
            print(e)
        return vis
        pass

    def draw(self, name:str, delay=100):
        """render graph as either a png or gif, depending on frame count."""
        name = f'{name}.gif'
        if len(self.frames) == 1:
            self.frames[0].layout('dot')
            return self.frames[0].draw(name, format='gif')

        filecount = len(self.frames)
        #print(f'making {filecount} frame files')
        files = [tempfile.NamedTemporaryFile(suffix='.png') for _ in range(filecount)]
        for i, g in enumerate(self.frames):
            g.layout('dot')
            g.draw(files[i].name)
        cmd = ['magick']
        for file in files:
            cmd.extend(( '-delay', str(delay), file.name))
        cmd.append(name)
        #print(' '.join(cmd))
        subprocess.call(cmd)
        print(f'wrote {filecount} frames to {name!r}')
        for f in files:
            f.close()

    def __getattr__(self, name):
        return getattr(self.frames[-1], name)

    def add_frame(self, data:int|vis_enabled=-1):
        """add a new frame to the graph animation based on a previous one."""
        if isinstance(data, int):
            new = self.frames[data].copy()
        else:
            new = normalize(data)
        self.frames.append(new)

    def attr(self, __t, __h=None, /, **attrs):
        if __h is None:
            self.frames[-1].add_node(__t, **attrs)
        else:
            self.frames[-1].add_edge(__t, __h, **attrs)

def vis_ast(ast:node, source:str|None=None):
    """Visualize an abstract syntax tree as a directed graph."""
    dg = gz.AGraph(directed=True)
    id = map(str, count())
    def walk(ast, i):
        match ast:
            case node():
                dg.add_node(i, label=ast.kind)
                for ia,(a, I) in enumerate(zip(ast, id)):
                    walk(a, I)
                    dg.add_edge(i, I, label=str(ia))
            case tuple():
                dg.add_node(i, label='()')
                for ia,(a, I) in enumerate(zip(ast, id)):
                    walk(a, I)
                    dg.add_edge(i, I, label=str(ia))
            case _:
                dg.add_node(i, label=repr(ast))
    walk(ast, next(id))
    if source:
        i = next(id)
        l:str = source.replace('\n', '\\l')
        if not l.endswith('\\l'):
            l += '\\l'
        dg.add_node(i, shape='box', label=l, labelloc='t')
    return dg


def palette(n, s=0.5, v=0.5):
    """generate n equally spaced HSL colors. Hopefully they're unique enough"""
    h = 360 * random.random()
    step = 360/n
    for _ in range(n):
        h = (h + step) % 360
        s = min(max(20, random.gauss(80, 60)), 100)
        l = min(max(40, random.gauss(80, 60)), 90)
        yield f'hsl({h}, {s}%, {l}%)'

def vis_highlight(source:str, P:parser.PackratParser, outfile='highlight.html'):
    """Generate html that shows rough syntax highlighting of a parse tree."""
    ast = P(source)
    if ast is None:
        # TODO
        print("TODO highlight can't visualize errors yet")
        return
    def tohtml(n:node):
        body = []
        last = slice(n.start)
        for a in n:
            match a:
                case str():
                    body.append(source[last.stop:last.stop+len(a)])
                    last = slice(last.stop + len(a))
                case node():
                    body.append(source[last.stop:a.start])
                    last = a
                    body.append(tohtml(a))
        if last:
            body.append(source[last.stop:n.stop])
        return f"<span class={n.kind!r} start={n.start} stop={n.stop}>{''.join(body)}</span>"

    kinds = set()
    def find_kinds(n):
        if isinstance(n, node):
            kinds.add(n.kind)
            for x in n:
                find_kinds(x)
    find_kinds(ast)
    
    body = tohtml(ast).replace('\n','↵<br>')
    css = ''.join(
        f'.{node} {{background-color: {color};}}'
        for node, color in zip(kinds, palette(len(kinds))))
    legend = ' '.join(f'<span class={kind!r}>{kind}</span>' for kind in kinds)

    with open(outfile, 'w') as f:
        f.write(f"""<!DOCTYPE html>
    <html>
      <head>
        <title>Syntax Highlighting</title>
        <style>
          span {{
            border-style: solid;
            border-radius: 10px;
            border-color: black;
            border-width: 1px;
            line-height: 24px;
            padding: 2px;
            }}
          {css}
        </style>
      </head>
      <body>
        Legend: {legend}
        <hr>
        <p>{body}</p>
      </body>
    </html>
    """)


if __name__=="__main__":
    import graph
    import testlang
    vis_highlight(testlang.sample, testlang.parser)
    
    #vis(testlang.sample_ast, testlang.sample).render(outfile='ast.png', cleanup=True, format='png')
    Vis(testlang.sample_ast).draw('ast')
    Vis.from_eval(testlang.TestEval(), testlang.sample_ast).draw('calc')

    m = graph.Graph()
    G = nx.DiGraph()
    G.add_edge('a', 'b')
    G.add_edge('b', 'c')
    G.add_edge('a', 'c')
    v = Vis()
    m.run(G, v)
    v.draw('compute')
    quit()
    # name resolution / computation graph generation
    names = evaluator.namespace() # comp hashes, keyed by a name which currently refer to them
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
                comp = model.add_node(comp, *dep)
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
    x(testlang.sample_ast)
    
    Vis(model).gif('compute')
