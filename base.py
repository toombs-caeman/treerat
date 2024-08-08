import abc

class ParseError(Exception):
    """raised if a parser fails on input while in strict mode."""

class CompileError(Exception):
    """raised if compile step fails unexpectedly."""

class EvalError(Exception):
    """raised if an evaluator fails unexpectedly."""

class node:
    """
    Generic tree node with some metadata.

    kind is an identifier of the kind of node.
    start and stop are indices into the source code such that source[start:stop] is the span covered by this node.
    """
    __slots__ = ['kind', 'start', 'stop', 'children']
    def __init__(self, kind, *children, start:int=..., stop:int=...):
        self.kind = kind
        self.start = start
        self.stop = stop
        self.children = children
    def __iter__(self):
        return iter(self.children)
    def __getitem__(self, __key):
        return self.children[__key]
    def __hash__(self):
        return hash((self.kind, self.children))
    def __eq__(self, __o):
        return isinstance(__o, node) and self.kind == __o.kind and self.children == __o.children
    def __repr__(self):
        return f'{type(self).__name__}{(self.kind, *self.children)!r}'
    def __str__(self):
        return f'{self.kind}[{self.start}:{self.stop}]'

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

    def __contains__(self, key):
        return any(key in n for n in self.__nro)

    def __setitem__(self, key, value):
        self.__nro[-1][key] = value

    def __enter__(self):
        self.__nro.append({})
        return self

    def __exit__(self, *_):
        return self.__nro.pop()

class Visualizer(abc.ABC):
    """Base class for graph visualizations."""
    wait  = 'black' # computation is not ready, black is the default color
    ready = 'blue'  # computation is ready to proceed
    active= 'green' # computation is active during this step
    done  = 'gray'  # computation is complete
    error = 'red'   # computation halted

    @abc.abstractmethod
    def add_frame(self, data=None):
        """add a new frame to the animation."""

    @abc.abstractmethod
    def attr(self, __t, __h=None, /, **attrs):
        """add attributes to node or edge."""

class NoVis(Visualizer):
    """Stub for when visualization is turned off."""
    def noop(self, *args, **kwargs):
        """don't do anything"""
    attr = add_frame = noop
    def __getattr__(self, name):
        return self.noop
    def __bool__(self):
        return False
    
class Parser(abc.ABC):
    """Base class for parsers."""
    @abc.abstractmethod
    def __call__(self, text:str, vis:Visualizer=NoVis(), strict=False):
        pass

class Evaluator(abc.ABC):
    """
    Base class for evaluators.

    In general an evaluator embodies the semantics of a language.
    Each evaluator receives an AST and does the computation represented by the AST.
    Subclasses of Evaluator should implement the __call__() method to do this.

    As a general pattern (not all evaluators have to do this), each recognized type of node
    should have a corresponding method in the evaluator to implement the semantics of that node.
    This makes it relatively straightforward to extend an Evaluator through subclassing.

    Evaluators should raise a RuntimeError if the ast they receive is invalid.

    vis is an optional visualizer, if present, each step of computation should be shown.
    """
    @abc.abstractmethod
    def __call__(self, ast:node, vis:Visualizer=NoVis()):
        self.vis = vis
        raise NotImplementedError


class Language(abc.ABC):
    parser:Parser
    evaluator:Evaluator
    prompt = '> '
    def __call__(self, text):
        return self.evaluator(self.parser(text, strict=True))
    def repl(self):
        """
        A stock standard read eval print loop (REPL).

        This doesn't let you input multi-line expressions,
        since there's no good way to detect that should be done from the grammar.
        """
        # enable readline if it's available
        try:
            import readline
        except ImportError:
            pass
        # loop
        while True:
            try:
                # read then eval
                value = self(input(self.prompt))
                # print
                if value is not None:
                    print(value)
            except (ParseError, CompileError, EvalError) as e:
                print(e)
            except (KeyboardInterrupt, EOFError):
                break



