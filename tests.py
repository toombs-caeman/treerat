#!/usr/bin/env python
import time
import unittest
from base import ParseError
from parser import fixedpoint, PackratParser, node, ast2labels


class TestParser(unittest.TestCase):

    def testFixedPoint(self):
        """
        Show that the manually initialized fixed point parser parses fixedpoint.tr into a parser exactly the same as the manually written one.

        This is essential, as it proves the initial premise of the parser, that it can fully describe (and therefore fully replace) its own grammar.
        """
        P = PackratParser()
        with open('fixedpoint.tr', 'r') as f:
            lines = f.readlines()

        simple = 'a <- ( b cd)'
        tree = P(simple)
        self.assertEqual(
                node('start', (node('Definition', node('Label', 'a'), node('Sequence', node('Label', 'b'), node('Label', 'cd'))),)),
                tree,
                msg=f'simple test case failed: {simple!r}'
        )

        # double check that the first line of the fixed point parses as expected
        tree = P(lines[0]) # lines[0]
        self.assertEqual(
                node('start', (
                    node(
                        'Definition',
                        node('Node', node('Label', 'start')),
                        node(
                            'Sequence',
                            node('Label', 'Spacing'),
                            node('Argument', node('OneOrMore', node('Label', 'Definition'))),
                            node('Label', 'EOF'))),)),
                tree,
                msg=f'could not parse line {lines[0]!r}'
        )

        # find any lines that don't parse individually
        for line in lines:
            # blank lines and comments shouldn't parse by themselves, so ignore them
            if line == '\n' or line.startswith('#'):
                continue
            tree = P(line)
            self.assertIsNotNone(tree, msg=f'could not parse line {line!r}')
            new_labels = ast2labels(tree)
            for k,v in new_labels.items():
                self.assertEqual(fixedpoint[k], v, msg=f'label {k!r} deviates from fixed point.')

        # check the full circle
        tree = P(''.join(lines))
        #pp(tree)
        self.assertIsNotNone(tree, msg=f'could parse individual lines, but not consecutive ones?')
        self.assertEqual(
                fixedpoint,
                ast2labels(tree),
                msg="fixed point not fixed, circle != square"
        )

    @unittest.skip('make forward parsing solid first')
    def testInverseParse(self):
        """
        Try re-formatting a parse tree back into code using a different parser than what generated it

        This is the inverse operation of parsing (also called fmt?)
        """
        # given a spec and valid parse tree, format the tree back into a string
        test_ok = {
                'a':PackratParser(start=node('Argument', node('Dot'))),
        }
        for code, P in test_ok.items():
            tree = P(code)
            self.assertIsNotNone(tree, msg="precondition failed: input not parsed")
            self.assertEqual(code, P.fmt(tree), msg="parse•fmt does not form fixed point")

        test_fail = {
                PackratParser(start=node('Argument', node('Dot'))): None,
        }
        for P, tree in test_fail.items():
            self.assertIsNone(P.fmt(tree), msg="Non-conforming input should be rejected")


    def testBuildMath(self):
        """Try building a parser in the initial language that recognizes math expressions with proper precedence."""
        math_lang = """
        %start <- %Expr !.
        Expr    <- (%Add / %Sub) / (%Mul / %Div) / '(' %Expr ')' / %Value
        %Add     <- %Expr:1 '+' %Expr
        %Sub     <- %Expr:1 '-' %Expr
        %Mul     <- %Expr:2 ('*' %Expr:1)+
        %Div     <- %Expr:2 ('/' %Expr:1)+
        %Value   <- %[0-9]+
        """
        P = PackratParser(math_lang)

        tests = {
            '6*7+3':node('start', node('Add', node('Mul', node('Value', '6'), node('Value', '7')), node('Value', '3'))),
            '1+2+3':node('start', node('Add', node('Value', '1'), node('Add', node('Value', '2'), node('Value', '3')))),
        }
        for input, expected in tests.items():
            actual = P(input)
            self.assertIsNotNone(actual, msg=f'could not parse input {input!r}')
            self.assertEqual(expected, actual, msg=f'incorrect parsing for input {input!r}')

    def testErrorReport(self):
        P = PackratParser()
        self.assertIsNone(P('bogus <- 123'), msg=f'should not have been able to parse malformed string')
        self.assertIsNotNone(P.error, msg='failing to parse should have generated an error message')
        # TODO this should capture more than just the first error. needs to have sync token

    @unittest.skip("this takes a long time and doesn't work yet")
    def testCache(self):
        # try to test how efficient caching is.
        P = PackratParser(
            """
            %start <- SPACE? (%word SPACE?)+ EOF
            %word <- 'bird'
            SPACE <- ' '+
            EOF <- !.
            """)
        string = 'bird'
        i = 0
        t0 = time.time()
        try:
            for i in range(1000):
                x = P(string)
                #print(x)
                self.assertIsNotNone(x)
                string += ' bird'
        except KeyboardInterrupt:
            pass #t = time.time() - t0
        t = time.time() - t0
        print(f'succeeded in {i} iterations in {t} seconds.')
        # with functools.cache is about 6.4 seconds
        self.assertLessEqual(t, 2, msg=f'time for parsing 1000 iterations should be less than 2 seconds')
        # TODO
    def testLeftRecursion(self):
        # the parser shouldn't hang or crash if given a mutually left recursive grammar
        P = PackratParser("a <- a ' '")
        self.assertRaises(ParseError, P, '   ')




if __name__ == "__main__":
    unittest.main()

