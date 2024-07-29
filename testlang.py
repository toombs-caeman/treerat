import parser

grammar = """
%Entrypoint <- EOL (%Assign / %Print)* !.
%Assign <- %Var EQUAL %Expr EOL
%Print   <- %Expr EOL

Expr    <- (%Add / %Sub) / (%Mul / %Div) / OPEN %Expr CLOSE / %Float / %Int / %Var
%Add    <- %Expr:1 PLUS %Expr
%Sub    <- %Expr:1 MINUS %Expr
%Mul    <- %Expr:2 (STAR %Expr:1)+
%Div    <- %Expr:2 (SLASH %Expr:1)+
%Float  <- %([0-9]+ '.' [0-9]+) SPACE
%Int    <- %[0-9]+ SPACE
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
parser = parser.BuildParser(**parser.squaredCircle(parser.fixedpoint.parse(grammar)))

sample = """
        x = 1 + 2
        x + 1
        x = x + 2
        x * 3.14
    """
sample_ast = parser.parse(sample)
