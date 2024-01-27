#!/usr/bin/env python
import unittest
from parser import *
from pprint import pprint as pp


class TestParser(unittest.TestCase):
    az = 'abcdefghijklmnopqrstuvwxyz_'
    AZ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    d  = '0123456789'
    var = [T.Sequence, [T.String, *az, *AZ], [T.ZeroOrMore, [T.String, *az, *AZ, *d]]]
    space = [T.String, ' ']
    lvar = [T.Label, 'var']
    avar = [T.Argument, var]
    nvar= [T.Node, 'var', avar]
    anvar = [T.Argument, nvar]
    lvar_lvar = [T.Sequence, lvar, space, lvar]
    nvar_nvar = [T.Sequence, nvar, space, nvar]
    anvar_anvar = [T.Sequence, anvar, space, anvar]
    nvarvar = [T.Node, 'varvar', anvar_anvar]

    def testFixedPoint(self):
        parse = fixedpoint.parse
        with open('fixedpoint.tr', 'r') as f:
            lines = f.readlines()

        # double check that the first line parses as expected
        tree = parse(lines[0]) # lines[0]
        self.assertEqual(
                tree,
                ['Entrypoint',
                 ['Definition',
                  ['Node', ['Label', 'Entrypoint']],
                  ['Sequence',
                   ['Label', 'Spacing'],
                   ['OneOrMore', ['Argument', ['Label', 'Definition']]],
                   ['Label', 'EOF']
                ]]],
        )
        # check that this parsing is a fixed point
        tree = squaredCircle(tree)[C.Entrypoint.name]
        self.assertEqual(labels[C.Entrypoint.name], tree)

        # find any lines that don't parse individually
        for line in lines:
            self.assertIsNotNone(parse(line), line)

        # TODO check the full circle
        return
        tree = parse(''.join(lines))
        pp(tree)
        self.assertEqual(
                tree,
                ['nonce'],
                msg="fixed point not fixed"
        )

    @unittest.skip('not working on this yet')
    def testInverseParse(self):
        # given a spec and valid parse tree, format the tree back into a string
        p = BuildParser([T.Dot])
        #self.assertEqual(p.parse('abcd'), 'a')
        self.assertEqual(p.fmt('a'), 'a')
        self.assertEqual(p.fmt('ab'), None, msg="Non-conforming input should be rejected")
        return
        p = BuildParser(self.nvarvar, var=self.nvar)
        tree = ['varvar', ['var', 'abc'], ['var', 'def']]
        self.assertEqual(p.fmt(tree), 'abc def')
        self.assertEqual(p.fmt(None), '')

        p = BuildParser(self.var)
        self.assertEqual(p.fmt('ab1cd'), 'ab1cd')
        self.assertRaises(ValueError, p.fmt, 'abcd*')
        self.assertEqual(ValueError, p.fmt, None)

    def testBuild(self):
        p = BuildParser(self.var)
        self.assertEqual(p.parse('ab1cd*'), 'ab1cd')
        self.assertEqual(p.parse('*asdf'), None)

        self.assertEqual(
            BuildParser(self.lvar_lvar, var=self.nvar).parse('abc def'),
            [['var', 'abc'], ' ', ['var', 'def']],
        )

        self.assertEqual(
            BuildParser(self.nvarvar, var=self.nvar).parse('abc def'),
            ['varvar', ['var', 'abc'], ['var', 'def']],
        )
    def testConformance(self):
        p = PackratParser
        for t in T:
            self.assertIn(t.name, dir(p), msg=f'{p.__name__} does not implement {t.name}')


if __name__ == "__main__":
    unittest.main()

