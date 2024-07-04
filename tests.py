#!/usr/bin/env python
import unittest
from parser import *
from pprint import pprint as pp


class Run(unittest.TestCase):

    def testFixedPoint(self):
        """
        Show that the manually initialized fixed point parser parses fixedpoint.tr into a parser exactly the same as the manually written one.

        This is essential, as it proves the initial premise of the language, that it can fully describe (and therefore fully modify) its own grammar.
        """
        parse = fixedpoint.parse
        with open('fixedpoint.tr', 'r') as f:
            lines = f.readlines()

        simple = 'a <- ( b cd)'
        tree = parse(simple)
        self.assertEqual(
                ['Entrypoint',
                ['Definition', ['Label', 'a'], ['Sequence', ['Label', 'b'], ['Label', 'cd']]]],
                tree,
                msg=f'simple test case failed: {simple!r}'
        )

        # double check that the first line of the fixed point parses as expected
        tree = parse(lines[0]) # lines[0]
        #pp(tree)
        self.assertEqual(
                ['Entrypoint',
                 ['Definition',
                  ['Node', ['Label', 'Entrypoint']],
                  ['Sequence',
                   ['Label', 'Spacing'],
                   ['Argument', ['OneOrMore', ['Label', 'Definition']]],
                   ['Label', 'EOF']
                ]]],
                tree,
                msg=f'could not parse line {lines[0]!r}'
        )

        # find any lines that don't parse individually
        for line in lines:
            # blank lines and comments shouldn't parse by themselves, so ignore them
            if line == '\n' or line.startswith('#'):
                continue
            tree = parse(line)
            self.assertIsNotNone(tree, msg=f'could not parse line {line!r}')
            new_labels = squaredCircle(tree)
            for k,v in new_labels.items():
                self.assertEqual(labels[k], v, msg=f'label {k!r} deviates from fixed point.')

        # check the full circle
        tree = parse(''.join(lines))
        #pp(tree)
        self.assertIsNotNone(tree, msg=f'could parse individual lines, but not consecutive ones?')
        self.assertEqual(
                labels,
                squaredCircle(tree),
                msg="fixed point not fixed, circle != square"
        )

    @unittest.skip('not working on this yet')
    def testInverseParse(self):
        """
        Try re-formatting a parse tree back into code using a different parser than what generated it

        This is the inverse operation of parsing (also called fmt?)
        """
        # given a spec and valid parse tree, format the tree back into a string
        p = BuildParser([T.Dot])
        #self.assertEqual(p.parse('abcd'), 'a')
        self.assertEqual(p.fmt('a'), 'a')
        self.assertEqual(p.fmt('ab'), None, msg="Non-conforming input should be rejected")
        return


    def testBuildMath(self):
        """Try building a parser in the initial language that recognizes math expressions with proper precedence."""
        def build(code, base_parser=fixedpoint):
            return BuildParser(**squaredCircle(base_parser.parse(code)))
        math_lang = """
        %Entrypoint <- %Expr !.
        Expr    <- (%Add / %Sub) / (%Mul / %Div) / '(' %Expr ')' / %Value
        %Add     <- %Expr:1 '+' %Expr
        %Sub     <- %Expr:1 '-' %Expr
        %Mul     <- %Expr:2 ('*' %Expr:1)+
        %Div     <- %Expr:2 ('/' %Expr:1)+
        %Value   <- %[0-9]+
        """
        mp = build(math_lang)

        tests = {
            '6*7+3':['Entrypoint', ['Add', ['Mul', ['Value', '6'], ['Value', '7']], ['Value', '3']]],
            '1+2+3':['Entrypoint', ['Add', ['Value', '1'], ['Add', ['Value', '2'], ['Value', '3']]]],
        }
        for input, expected in tests.items():
            actual = mp.parse(input)
            self.assertIsNotNone(actual, msg=f'could not parse input {input!r}')
            self.assertEqual(expected, actual, msg=f'incorrect parsing for input {input!r}')


    def testConformance(self):
        """Show that the parser conforms to the interface in T (the 'spec' spec)."""
        p = PackratParser
        for t in T:
            self.assertTrue(t.name in dir(p), msg=f'{p.__name__} does not implement {t.name}')


if __name__ == "__main__":
    unittest.main()

