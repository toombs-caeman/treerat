import parser

grammar = """
%Entrypoint <- EOL (%Statement)* !.
Statement   <- %Print / %Assign / %Expr EOL
%Assign     <- %Var EQUAL %Expr EOL
%Print      <- PRINT %Expr EOL

Expr    <- (%Add / %Sub) / (%Mul / %Div) / %Float / %Int / %Var / %Scope / OPEN %Expr CLOSE
%Add    <- %Expr:1 PLUS %Expr
%Sub    <- %Expr:1 MINUS %Expr
%Mul    <- %Expr:2 (STAR %Expr:1)+
%Div    <- %Expr:2 (SLASH %Expr:1)+
%Float  <- %([0-9]+ '.' [0-9]+) SPACE
%Int    <- %[0-9]+ SPACE
%Var    <- %[a-z]+ SPACE
%Scope  <- LB (%Statement)+ RB

PRINT   <- 'print' SPACE
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
EOL     <- [; \\n]*
"""
parser = parser.BuildParser(**parser.squaredCircle(parser.fixedpoint.parse(grammar)))

sample = """
x = 1 + 2
print x + 1
    print { x = 4; x;}
x = x + 2
x * 3.14"""
sample_ast = parser.parse(sample)
if sample_ast is None:
    print('parse of testlang failed')
