# mypy: disable-error-code="empty-body"
from typing import TypeAlias

from egglog import *

NumLike: TypeAlias = 'Num | StringLike | i64Like'

class Num(Expr):
    def __init__(self, value:i64Like): ...
    def __add__(self, other:NumLike) -> 'Num': ...
    def __mul__(self, other:NumLike) -> 'Num': ...
    def __radd__(self, other: NumLike) -> 'Num': ...
    def __rmul__(self, other: NumLike) -> 'Num': ...
    @classmethod
    def var(cls, name: StringLike) -> 'Num': ...

converter(i64, Num, Num)
converter(String, Num, Num.var)

e = EGraph()

@e.register
def _(a:Num, b:Num):
    yield rewrite(a + b).to(b + a)
    yield rewrite(a * b).to(b * a)
@e.register
def _(a:Num, b:Num, c:Num):
    yield rewrite((a * b) * c).to(a * (b * c))
@e.register
def _const_fold(a: i64, b: i64):
    yield rewrite(Num(a) + Num(b)).to(Num(a + b))
    yield rewrite(Num(a) * Num(b)).to(Num(a * b))

x = Num.var("x")
expr1 = e.let("expr1", 2 * (x * 3))
expr2 = e.let("expr2", 6 * x)
e.saturate()
e.display()
