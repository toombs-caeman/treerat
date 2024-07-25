from parser import fixedpoint, T
import functools
class Evaluator:
    def __init__(self):
        self.parser = fixedpoint

        self.nodes = {}

    def eval(self, code):
        tree = self.parser.parse(code)
        if tree is None:
            raise ValueError("couldn't parse input")
        return self(tree)
    def __call__(self, tree):
        t, *args = tree
        if not hasattr(self, t):
            raise KeyError(f"evaluator does not implement node {t}")
        return getattr(self, t)(*args)
    def Entrypoint(self, *args):
        for a in args:
            print(self(a))
    def Definition(self, lhand, rhand):
        match lhand:
            case [T.Node.name, [T.Label.name, name]]:
                pass
            case [T.Label.name, name]:
                pass
            case _:
                raise ValueError(f'unexpected lhand {lhand}')
        print(f'updating parse rule {name}')
        self.parser.update(**{name:[T.Node.name, name, rhand]})

if __name__ == "__main__":
    e = Evaluator()
    e.eval("""
        %Entrypoint <- Spacing %(Definition / clear)+ EOF
    """)
    e.eval('clear')


