#!/usr/bin/env python
import unittest
import treerat
from parser import *

class TestParser(unittest.TestCase):
    @unittest.skip('not implemented')
    def testFixedPoint(self):
        
        p = BuildParser(treerat.fp_spec, **treerat.fp_labels)
        
        self.assertEqual(
                p(treerat.fp),
                None,
                msg="fixed point not fixed"
        )

    az = 'abcdefghijklmnopqrstuvwxyz_'
    AZ = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ_'
    d  = '0123456789'
    var = [T.Sequence, [T.Choice, *az, *AZ], [T.ZeroOrMore, [T.Choice, *az, *AZ, *d]]]
    lvar = [T.Label, 'var']
    avar = [T.Argument, var]
    nvar= [T.Node, 'var', avar]
    anvar = [T.Argument, nvar]
    lvar_lvar = [T.Sequence, lvar, ' ', lvar]
    nvar_nvar = [T.Sequence, nvar, ' ', nvar]
    anvar_anvar = [T.Sequence, anvar, ' ', anvar]
    nvarvar = [T.Node, 'varvar', anvar_anvar]

    def testInverseParse(self):
        # given a spec and valid parse tree, format the tree back into a string
        p = BuildParser([T.Dot])
        #self.assertEqual(p('abcd'), 'a')
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
        self.assertEqual(p('ab1cd*'), 'ab1cd')
        self.assertEqual(p('*asdf'), None)

        self.assertEqual(
            BuildParser(self.lvar_lvar, var=self.nvar)('abc def'),
            [['var', 'abc'], ' ', ['var', 'def']],
        )

        self.assertEqual(
            BuildParser(self.nvarvar, var=self.nvar)('abc def'),
            ['varvar', ['var', 'abc'], ['var', 'def']],
        )
    def testConformance(self):
        p = PackratParser
        for t in T:
            self.assertIn(t.name, dir(p), msg=f'{p.__name__} does not implement {t.name}')


if __name__ == "__main__":
    unittest.main()

