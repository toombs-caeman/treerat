from base import *

class TreeWalk(Evaluator):
    """
    A base class for tree walk evaluators.
    Each method receives unevaluated arguments to the corresponding AST node and should return the evaluated expression.
    The methods can call self.eval() to evaluate their arguments.

    TODO:
        replicate in javascript
        add a small example down below
    """
    def __init__(self, fast=False):
        self.fast = fast
        self.names = namespace()
    def __call__(self, ast:node, vis:Visualizer=NoVis()):
        self.__fast = False
        self.vis = vis
        vis.add_frame(ast)
        # let eval short-circuit a bunch of stuff sometimes
        # fast is relative, tree-walking is never super fast
        self.__fast = self.fast and isinstance(vis, NoVis)
        return self.eval(ast)

    def eval(self, ast:node):
        if self.__fast:
            # short-circuits checks and visualizations
            # just do the thing
            return getattr(self, ast.kind)(*ast)
        if not isinstance(ast, node):
            raise EvalError(f'eval of non-ast value {ast!r}.')
        op = ast.kind
        if not hasattr(self, op):
            self.vis.attr(ast, color=self.vis.error)
            raise EvalError(f'unrecognized ast type {op}: {ast!r}')

        # mark the current node and its edges as active
        self.vis.attr(ast, color=self.vis.active)
        for a in ast:
            if isinstance(a, node):
                self.vis.attr(ast, a, color=self.vis.active)
        self.vis.add_frame()

        # eval the node
        value = getattr(self, op)(*ast)

        # mark the node and its edges as done
        self.vis.attr(ast, color=self.vis.done)
        for a in ast:
            if isinstance(a, node):
                self.vis.attr(ast, a, color=self.vis.done)
        self.vis.add_frame()

        return value
