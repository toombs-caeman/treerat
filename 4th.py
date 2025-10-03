import re
from typing import Callable, Generator, Mapping

__all__ = ['munge', 'prep']

class prep[T]:
    """processes a string into a list of tokens"""
    def __init__(self, patterns:Mapping[str,Callable[[str], T]]):
        self.pattern = re.compile('|'.join(f'({p})' for p in patterns))
        self.types = tuple(patterns.values())
        assert self.pattern.groups == len(self.types), "none of the passed patterns should contain groups"
    def __call__(self, s:str) -> Generator[T]:
        return (
            self.types[m.lastindex-1](m[m.lastindex])
            for m in self.pattern.finditer(s)
            # This condition is only needed to make the typechecker happy.
            # It's impossible for there to be a match, but not match any group
            # based on how the pattern is constructed.
            if m.lastindex is not None
        )

def test_preprocessor():
    words = prep({r'\S+': str})
    for test in [
        'here we go.',
        'these words are being split on spaces.',
        "it wouldn't quite work the same around newlines, but idk."
    ]:
        assert list(words(test)) == test.split(' ')

    num = prep({
        r'\d+\.\d*': float,
        r'\d+': int,
        r'\w+': str,
    })

    for input, result in {
        'this should be 5 words.': ['this', 'should', 'be', 5, 'words'],
        'float=5.5 3 4': ['float', 5.5, 3, 4]
    }.items():
        assert result == list(num(input))



words = {}

def word(f, n=None):
    "register words"
    if isinstance(f, str):
        return lambda f:word(f,n)
    if n is None:
        n = f.__name__
    words[n] = f
    return f

def munge(s:str):
    left, right = s.split(':')
    right = tuple(-1-int(d) for d in right)
    if not left:
        return lambda stack: stack.extend(stack[i] for i in right)

    left = -int(left)
    def _(stack):
        stack[left:] = (stack[i] for i in right)
    return _

def test_munge():
    input = (0, 1, 2, 3, 4)
    for pattern, output in {
        '0:': [], # clear
        '1:': [0, 1, 2, 3], # drop
        '2:': [0, 1, 2], # drop drop
        ':0': [0, 1, 2, 3, 4, 4], # dup
        ':00': [0, 1, 2, 3, 4, 4, 4], # dup dup
        ':1': [0, 1, 2, 3, 4, 3], # over
        '2:01': [0, 1, 2, 4, 3], # swap
        '3:102': [0, 1, 3, 4, 2], # rot
        '3:02': [0, 1, 4, 2], # swap drop swap
    }.items():
        i = list(input)
        munge(pattern)(i)
        assert i == output, f'{pattern=}'


