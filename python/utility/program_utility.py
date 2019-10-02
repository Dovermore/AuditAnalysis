from os import path

from matplotlib import pyplot as plt

from collections import OrderedDict as PythonOrderedDict
from functools import partial

import os


import functools
import weakref


# https://stackoverflow.com/questions/33672412/python-functools-lru-cache-with-class-methods-release-object
def memoized_method(*lru_args, **lru_kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(self, *args, **kwargs):
            # We're storing the wrapped method inside the instance. If we had
            # a strong reference to self the instance would never die.
            self_weak = weakref.ref(self)
            @functools.wraps(func)
            @functools.lru_cache(*lru_args, **lru_kwargs)
            def cached_method(*args, **kwargs):
                return func(self_weak(), *args, **kwargs)
            setattr(self, func.__name__, cached_method)
            return cached_method(*args, **kwargs)
        return wrapped_func
    return decorator


class Cached:
    """ Turn a function to class instance of Cached class and
        cache result whenever any one calles the new function

        In this Example it is used for ackermann function
        Note here, the wrapped function is no longer a Function, but rather a
        instance of class Cached.

        1. ack = Cached(ack(x, y)) --> already a instance of Cached
           1.1 ack.function = ack(x, y)
           1.2 ack.cache = {}
        2. ack(1, 1) -> calls the __call__ method because its an instance
        3. the dictionary is filled with the recursive calls

        (4. imagine using this for a prime number finder, it can auto cache the
            prime number found,and the time of calculation is greatly shortened
            by refereing to previous function results in dictionary)
    """
    def __init__(self, function):
        self.function = function
        self.cache = {}

    def __call__(self, *args, **kwargs):
        sorted_kwargs = tuple(sorted(kwargs.items()))
        try:
            cached_value = self.cache[(args, sorted_kwargs)]
            return cached_value
        except KeyError:
            ret = self.cache[(args, sorted_kwargs)] = self.function(*args, **kwargs)
            return ret


class CachedMethod:
    """cache the return value of a method
    
    This class is meant to be used as a decorator of methods. The return value
    from a given method invocation will be cached on the instance whose method
    was invoked. All arguments passed to a method decorated with memoize must
    be hashable.
    
    If a memoized method is invoked directly on its class the result will not
    be cached. Instead the method will be invoked like a static method:
    class Obj(object):
        @memoize
        def add_to(self, arg):
            return self + arg
    Obj.add_to(1) # not enough arguments
    Obj.add_to(1, 2) # returns 3, result is not cached
    """
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self.func
        return partial(self, obj)

    def __call__(self, *args, **kw):
        obj = args[0]
        try:
            cache = obj.__cache
        except AttributeError:
            cache = obj.__cache = {}
        key = (self.func, args[1:], frozenset(kw.items()))
        try:
            res = cache[key]
        except KeyError:
            res = cache[key] = self.func(*args, **kw)
        return res


class OrderedDict(PythonOrderedDict):
    def append(self, key, value):
        # Didn't find
        try:
            self[key] += value
        except KeyError:
            self[key] = value

    def peek(self, last=False):
        if last:
            k = next(reversed(self))
        else:
            k = next(iter(self))
        return k, self[k]


class SimpleProgressionBar:
    _prefix_format = "{0:6}/{1:6}"
    _bar_format = "|{:<20}|"
    
    def __init__(self, n):
        self._n = n
        self._prev = ""

    def __call__(self, x):
        solid = x*20//self._n
        prefix = self._prefix_format.format(x, self._n)
        bar = self._bar_format.format(u"\u25A0" * solid + u"\u25A1" *
                                      (20-solid))
        self._prev = prefix + bar
        print("\r" + self._prev, end="")
        if x == self._n:
            print()


def pretty_print(sep=1, **kwargs):
    """
    Given variable name and value, and length to print, this function prints
    variables in a pretty way
    Args:
        sep (int): number of separation lines to print
    kwags (key: (value, length)): The pair of key value to print out,
    Note the printed value will always have a white space on both sides
    """
    key_string = ""
    value_string = ""
    sep_len = 0
    
    key_format = "| {:<%d} "
    value_format = "| {:<%d} "
    value_format_s = "| {:<%s} "
    val_f = ""
    for key in kwargs:
        if key == "sep":
            sep = sep
            continue
        if len(kwargs[key]) == 2:
            value, length = kwargs[key]
        else:
            value, length, val_f = kwargs[key]
        sep_len += length + 3
            
        new_key_format = key_format % length

        if len(kwargs[key]) == 2:
            new_value_format = value_format % length
        else:
            new_value_format = value_format_s % val_f

        key_string += new_key_format.format(key)
        value_string += new_value_format.format(value)
    sep_string = "-" * sep_len + "\n"
    print(key_string) 
    print(value_string) 
    print(sep_string * sep, end="")


class BatchFunctionWrapper:
    def __init__(self):
        self.partial_functions = []

    def add_call(self, fn, *args, **kwargs):
        self.partial_functions.append(
            partial(fn, *args, **kwargs)
        )

    def __call__(self, *args, **kwargs):
        results = []
        for partial_function in self.partial_functions:
            results.append(partial_function(*args, **kwargs))
        return results

    def __len__(self):
        return len(self.partial_functions)



def null_bar(x):
    """
    This progression bar is very lazy, and does nothing!
    """
    return None


def save_fig(fname, fig: plt.Figure = None, fpath=path.join("..", "figures")):
    if not path.exists(fpath):
        os.makedirs(fpath)
    to = path.join(fpath, fname)
    if fig is not None:
        fig.savefig(to)
        return
    plt.savefig(to)


def string_to_num(s):
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s

