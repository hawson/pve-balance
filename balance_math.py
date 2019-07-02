# My silly implementation of some basic math routines
# mostly on vectors of arbitrary length
'''Simple implementaion of some basic math/vector routines'''
from math import sqrt
from operator import mul
from functools import reduce

def dot(a, b):
    '''dot product of two vector of arbitrary, but equal number of elements'''
    return sum(map(mul, a, b))


def length(a):
    '''scalar length of a vector'''
    return  sqrt(sum(map(lambda x: x**2, a)))


def norm(a):
    '''normalized vector of unit length'''
    vector_length = length(a)
    return list(map(lambda x: x/vector_length, a))


def area(a):
    '''area of a vector'''
    return reduce(lambda acc, x: acc*x, a)
