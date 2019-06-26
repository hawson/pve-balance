# My silly implementation of some basic math routines
# mostly on vectors of arbitrary length
'''Simple implementaion of some basic math/vector routines'''
from math import sqrt
from operator import mul
from functools import reduce

# dot product of two vector of arbitrary, but equal length
def dot(a, b):
    return sum(map(mul, a, b))


def length(a):
    return  sqrt(sum(map(lambda x: x**2, a)))


def norm(a):
    vector_length = length(a)
    return list(map(lambda x: x/vector_length, a))


def area(a):
    return reduce(lambda acc, x: acc*x, a)
