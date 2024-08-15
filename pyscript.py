import parser
from itertools import count

from pyscript import document
import js
from pyscript.ffi import to_js, create_proxy
from pyscript.web.elements import span
from pyscript.web import dom


def node2graph(n):
    # prepare a node tree for visualization with vizjs
    edges = []
    nodes = []
    I = count()

    def N(n, i):
        match n:
            case parser.node():
                nodes.append({ 'name':i, 'attributes': { 'label':n.kind } })
                for child in n:
                    cid = next(I)
                    edges.append({'tail':i, 'head':cid})
                    N(child, cid)
            case tuple():
                nodes.append({'name':i, 'attributes': { 'label':'()'}})
                for child in n:
                    cid = next(I)
                    edges.append({'tail':i, 'head':cid})
                    N(child, cid)
            case _:
                nodes.append({
                    'name':i,
                    'attributes': {
                        'label':repr(n),
                        'shape':'box',
                    }
                })
    N(n, next(I))
    return {
            'directed': True,
            'edges': edges,
            'nodes': nodes
    }

def click_handler(event=None):
    text = document.querySelector('#grammar').value
    try:
        tree = parser.PackratParser()(text)
    except parser.ParseError:
        return
    js.graph = to_js(node2graph(tree))
    js.render(js.graph)

# create a parser object that follows the LDT api, but calls into our python parser
class Parser:
    def __init__(self):
        self.P = parser.PackratParser()

    def tokenize(self, source, grammar=None):
        try:
            if grammar is not None:
                self.P = parser.PackratParser(grammar)
            self.source = source
            self.kinds = set()



            tree = self.P(source)
        except parser.ParseError:
            return source
        js.console.log(repr(tree))
        if not tree:
            return source
        self.find_kinds(tree)
        legend = ' '.join(f'<span class={kind!r}>{kind}</span>' for kind in self.kinds)
        return self.tohtml(tree, tree.start, tree.stop)

    def tohtml(self, n:parser.node, start, stop):
        body = []
        if isinstance(n, tuple):
            last = slice(n[0].start)
        else:
            last = slice(n.start)
        for a in n:
            match a:
                case str():
                    body.append(self.source[last.stop:last.stop+len(a)])
                    last = slice(last.stop + len(a))
                case parser.node():
                    body.append(self.source[last.stop:a.start])
                    last = a
                    body.append(self.tohtml(a, a.start, a.stop))
                case tuple():
                    # TODO this is gross, properly handle tuples at the top level
                    for x in a:
                        match x:
                            case str():
                                body.append(self.source[last.stop:last.stop+len(x)])
                                last = slice(last.stop + len(x))
                            case parser.node():
                                body.append(self.source[last.stop:x.start])
                                last = x
                                body.append(self.tohtml(x, x.start, x.stop))
        if last:
            body.append(self.source[last.stop:n.stop])
        return f"<span class={n.kind!r} start={n.start} stop={n.stop}>{''.join(body)}</span>"


    def find_kinds(self, n):
        if isinstance(n, parser.node):
            self.kinds.add(n.kind)
            for x in n:
                self.find_kinds(x)
    

js.Gparser = create_proxy(Parser())
g = document.getElementById("grammar")
js.grammar = js.TextareaDecorator.new(g, js.Gparser, None);
js.Sparser = create_proxy(Parser())
js.code = js.TextareaDecorator.new(document.getElementById("source"), js.Sparser, g);

js.console.log('loaded the click handler')
