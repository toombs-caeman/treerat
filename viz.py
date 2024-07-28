# reference https://github.com/mapio/GraphvizAnim/blob/master/examples/dfv.py
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
        reset = -int(reset)
        self.__previous.append(copy.deepcopy(self))
        if reset:
            self.body = self.__previous[reset-1].body
    def gif(self, outfile:str, delay=100):
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



def build(code, base_parser=parser.fixedpoint):
    v = base_parser.parse(code)
    return parser.BuildParser(**parser.squaredCircle(v))

math_lang = """
%Entrypoint <- EOL (%Assign / %Print)* !.
%Assign <- %Var EQUAL %Expr EOL
%Print   <- %Expr EOL

Expr    <- (%Add / %Sub) / (%Mul / %Div) / OPEN %Expr CLOSE / %Float / %Int / %Var
%Add    <- %Expr:1 PLUS %Expr
%Sub    <- %Expr:1 MINUS %Expr
%Mul    <- %Expr:2 (STAR %Expr:1)+
%Div    <- %Expr:2 (SLASH %Expr:1)+
%Float  <- %([0-9]+ '.' [0-9]+) SPACE
%Int  <- %[0-9]+ SPACE
%Var    <- %[a-z]+ SPACE

OPEN    <- '(' SPACE
CLOSE   <- ')' SPACE
EQUAL   <- '=' SPACE
PLUS    <- '+' SPACE
MINUS   <- '-' SPACE
STAR    <- '*' SPACE
SLASH   <- '/' SPACE
SPACE   <- ' '*
EOL     <- [; \\n]*
"""
mp = build(math_lang)

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
    ast = mp.parse("""
        x = 1 + 2
        x + 1
        x = x + 2
        x * 3.14
    """)
    #print(ast)
    if ast is None:
        print('parse failed')
        quit()
    # visualize ast
    ast_viz(ast).render(outfile='ast.png', cleanup=True, format='png') #, view=True)

    # name resolution / computation graph generation
    names = {}
    comps = {} # units of computation, keyed by their hash
    order = defaultdict(set) # for each comp, keep a set of preceeding comps
    effects = [] # a sequence of computations with stateful effects
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



