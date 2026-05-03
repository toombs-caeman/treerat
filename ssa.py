from pika import Pika, ParseError
from grammar import Grammar

g = r"""
grammar <- (statement / blank)* EOF
statement <- sp (print / assignment / sexpr:(expr))
print <- printexpr:('print' sp expr EOL)
assignment <- assign:(identifier '=' sp expr EOL)
expr <-
    mul:(expr '*' sp expr) /
    div:(expr '/' sp expr) /
    add:(expr '+' sp expr) /
    sub:(expr '-' sp expr) /
    '(' sp expr ')' sp /
    number / identifier
identifier <- ident:([a-zA-Z_]+) sp
number <- int:([0-9]+) sp
EOL <- '\r\n' / '\n' / '\r' / EOF
EOF <- !.
blank <- sp EOL
sp <- [ \t]*
"""
#grammar = Grammar.from_ast(Pika().parse(g).ast(g))
parser = Pika(g)

if __name__ == "__main__":
    from pprint import pp
    test = """a=1 * 2 - 3 / 4
    --
    print a
    """
    # print(parser.spans(test))
    try:
        ast = list(parser.ast(test))
        pp(ast)
    except ParseError as e:
        # TODO prototype nice error messages
        if e.text is None or e.lineno is None or e.end_lineno is None or e.end_offset is None:
            raise e
        print('ParseError')
        lines = e.text.splitlines()
        first = max(0, e.lineno-2)
        last = min(len(lines), e.end_lineno+2)
        for i,l in enumerate(lines[first:last], first+1):
            print(l)
            if i < e.lineno or e.end_lineno < i:
                continue
            start = e.offset if i == e.lineno else 0
            stop = e.end_offset if i == e.end_lineno else len(l)
            print(f"{' ' * start}{'^'*(stop-start)}")
