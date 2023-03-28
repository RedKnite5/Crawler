
import typing
from typing import Literal

def double(x):
	return x + x

def foo(x: Literal[5, 6]):
	print(x)


foo(5)
g = 2
foo(double(g))


