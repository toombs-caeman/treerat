# 4-22
9-9.5: trim. need to be more strict about argument placement and trimming
10.5-11:

# 7-03
14-15.5:trim, adding explanatory logs
16-17:trim, tracking down fixed point deviations
21-22:tracking down fixed point deviations, 

strings need to be re-worked, since strings and character classes are distinct.
Arguably though, they are a special form of Sequence and Choice over Char

# 7-03
9.5-11: separate string from character class
11.5-13.5: separate string from character class, testBuildMath

# 8-03
put in a lot of time recently.

# 8-07
17.5-22: move parser.py trim into base function calls in order to prep translation to javascript

# 8-08
7-9:figure out how to more efficiently cache using difflib.SequenceMatcher.get_opcodes()
    * this sometimes fails when a definition ends in ZeroOrMore because its range appears unchanged, but it could consume more input if given the chance.

# 8-12
18.5-20: LDT and reading CI
20.5-23.5: defining specific traits and types for a core of toylang

# todo
* optim: make sure that trim isn't doing extraneous work
* optim: clean up parser internals to make them easier to reason about and port
