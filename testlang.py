from base import *
import parser
import tree

grammar = """
%start <- [; \\n]* (%Statement)* !.
Statement   <- %Print / %Assign / %Expr EOL
%Assign     <- %Var EQUAL %Expr EOL
%Print      <- PRINT %Expr EOL

Expr    <- (%Add / %Sub) / (%Mul / %Div) / %Float / %Int / %Def / %Call / %Var / %Scope / OPEN %Expr CLOSE
%Def    <- OPEN %Var (COMMA %Var)* CLOSE COLON %Expr
%Call   <- %Var OPEN %Expr (COMMA %Expr)* CLOSE
%Add    <- %Expr:1 PLUS %Expr
%Sub    <- %Expr:1 MINUS %Expr
%Mul    <- %Expr:2 (STAR %Expr:1)+
%Div    <- %Expr:2 (SLASH %Expr:1)+
%Float  <- %([0-9]+ '.' [0-9]+) SPACE
%Int    <- %[0-9]+ SPACE
%Var    <- %[a-z]+ SPACE
%Scope  <- LB (%Statement)+ RB

COLON   <- ':' SPACE
COMMA   <- SPACE ',' SPACE
PRINT   <- 'print ' SPACE
LB      <- '{' SPACE
RB      <- '}' SPACE
OPEN    <- '(' SPACE
CLOSE   <- ')' SPACE
EQUAL   <- '=' SPACE
PLUS    <- '+' SPACE
MINUS   <- '-' SPACE
STAR    <- '*' SPACE
SLASH   <- '/' SPACE
SPACE   <- ' '*
EOL     <- SPACE ([;\\n] EOL? / !.) SPACE
"""
parser = parser.PackratParser(grammar)

sample = """ x = 1 + 2
print x + 1
    print { x = 4; x;}
x = x + 2
x * 3.14"""
sample_ast = parser(sample)
if sample_ast is None:
    print('parse of testlang failed')
    print('\n'.join(parser.error))

class TestEval(tree.TreeWalk):
    def start(self, *stmts):
        v = None
        for s in stmts:
            v = self.eval(s)
        return v

    def Assign(self, var, expr):
        value = self.eval(expr)
        self.names[var[0]] = value
        # we don't explicitly evaluate this
        # but it should be marked as done
        self.vis.attr(var, color=self.vis.done)
        return value

    def Var(self, name):
        if name not in self.names:
            raise EvalError(f'undefined name: {name!r}')
        return self.names[name]

    def Scope(self, *stmts):
        v = None
        with self.names:
            for s in stmts:
                v = self.eval(s)
        return v

    def Print(self, expr):
        print(self.eval(expr))

    def Add(self, left, right):
        return self.eval(left) + self.eval(right)

    def Sub(self, left, right):
        return self.eval(left) - self.eval(right)

    def Mul(self, left, right):
        return self.eval(left) * self.eval(right)

    def Div(self, left, right):
        return self.eval(left) / self.eval(right)

    def Float(self, literal):
        return float(literal)

    def Int(self, literal):
        return int(literal)

    def Def(self, *exprs):
        *vars, expr = exprs
        freevars = [v[0] for v in vars]
        # create a namespace for the closure by enclosing all the names referenced
        # in the body of the function (except the freevars)
        closure = {v:None for v in freevars}
        def close(expr:node):
            if not isinstance(expr, node):
                return
            if expr.kind == 'Var' and expr[0] not in closure:
                closure[expr[0]] = self.eval(expr)
            for a in expr:
                close(a)
        close(expr)
        # define closure
        def func(*args):
            if len(args) != len(freevars):
                raise EvalError(f"function call expected {len(freevars)} arguments but got {len(args)}")
            values = [self.eval(a) for a in args]
            with self.names:
                for name, value in zip(freevars, values):
                    self.names[name] = value
                return self.eval(expr)
        return func

    def Call(self, var, *args):
        return self.eval(var)(*args)


class TestLang(Language):
    parser = parser
    evaluator = TestEval(fast=True)

if __name__ == "__main__":
    TestLang().repl()


