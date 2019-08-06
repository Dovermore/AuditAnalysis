import logging
import os
from os import path
os.environ["R_HOME"] = "/anaconda/envs/ml_env/lib/R"

from multiprocessing.managers import SyncManager, DictProxy
from matplotlib import pyplot as plt

# from scipy.stats import binom, hypergeom

from collections import defaultdict
from collections import deque
from functools import partial

import os


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
            # print("cached")
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


class OrderedDict:
    
    def __init__(self):
        # Priority queue for keys
        self._q = deque()
        
        # Dictionary for values
        self._dict = defaultdict(float)
        
    def append(self, key, value):
        print("Before:", key, value, self._q, self._dict)
        # Didn't find
        if key not in self._q:
            self._q.appendleft(key)
            self._dict[key] = value
        else:
            self._dict[key] += value
        print("After :", key, value, self._q, self._dict)

    def pop(self):
        key = self._q.pop()
        value = self._dict[key]
        del self._dict[key]
        return key, value

    def peek(self):
        logging.warning([str(self._q), str(self._dict)])
        key = self._q[-1]
        value = self._dict[key]
        return key, value
    
    def __repr__(self):
        return str([(key, self._dict[key]) for key in self._q])
    
    def serialize(self):
        return [(key, self._dict[key]) for key in self._q]

    def __len__(self):
        return len(self._q)


class CollectionsManager(SyncManager):
    pass


# class DefaultdictProxy:
#     def __init__(self, data_type):
#         self.defaultdict = defaultdict(data_type)
#
#     def __len__(self):
#         return self.defaultdict.__len__()
#
#     def __delitem__(self, v):
#         self.defaultdict.__delitem__(v)
#
#     def __getitem__(self, k):
#         self.defaultdict.__getitem__(k)
#
#     def __iter__(self):
#         return self.defaultdict.__iter__()
#
#     def __setitem__(self, k, v):
#         return self.defaultdict.__setitem__(k, v)
#
#     def clear(self):
#         return self.defaultdict.clear()
#
#     def copy(self):
#         return self.defaultdict.copy()
#
#     def items(self):
#         return self.defaultdict.items()
#
#     def keys(self):
#         return self.defaultdict.keys()
#
#     def pop(self, k):
#         return self.defaultdict.pop(k)
#
#     def popitem(self):
#         return self.defaultdict.popitem()
#
#     def setdefault(self, k, default):
#         return self.defaultdict.setdefault(k, default)
#
#     def update(self, __m, **kwargs):
#         return self.defaultdict.update(__m, **kwargs)
#
#     def values(self):
#         return self.defaultdict.values()
#
#     def __str__(self):
#         return self.defaultdict.__str__()


class DequeProxy:
    def __init__(self, *args):
        self.deque = deque(*args)

    def __len__(self):
        return self.deque.__len__()

    def appendleft(self, x):
        self.deque.appendleft(x)

    def append(self, x):
        self.deque.append(x)

    def pop(self):
        return self.deque.pop()

    def popleft(self):
        return self.deque.popleft()

    def __getitem__(self, k):
        return self.deque.__getitem__(k)

    def __str__(self):
        return self.deque.__str__()


CollectionsManager.register("deque", DequeProxy, exposed=["__len__", "append", "appendleft", "pop", "__getitem__",
                                                          "__str__", "popleft"])
# CollectionsManager.register("defaultdict", defaultdict, DefaultdictProxy)
CollectionsManager.register("defaultdict", defaultdict, DictProxy)


class AutoLockMultiprocessingOrderedDict(OrderedDict):
    """
    Adding locks for all operations
    """

    def __init__(self, mgr: CollectionsManager):
        """
        :param mgr: Manager for deque and defaultdict
        """
        # super().__init__()
        # Replace data structure with manager and multiprocessing safe data structures
        self._q = mgr.deque()
        self._dict = mgr.dict()
        self._lock = mgr.Lock()

    def append(self, key, value):
        with ContextTracker("append"):
            with self._lock:
                super().append(key, value)

    def pop(self):
        with self._lock:
            return super().pop()

    def peek(self):
        with self._lock:
            return super().peek()

    def __repr__(self):
        with self._lock:
            return super().__repr__()

    def serialize(self):
        with self._lock:
            return super().serialize()

    def __len__(self):
        with ContextTracker("len"):
            with self._lock:
                return super().__len__()

    def shutdown(self):
        self.mgr.shutdown()


def natural_number_generator():
    i = 0
    while True:
        yield i
        i += 1


class ContextTracker:
    identifier_subscript = natural_number_generator()
    enter_set = set()
    exit_set = set()

    def __init__(self, identifier):
        # FIXME there might be threading issue here as well
        self.identifier = str(identifier) + f"_{next(self.identifier_subscript)}"

    def __enter__(self):
        self.enter_set.add(self.identifier)
        logging.debug(f"Enter message: {self.identifier}")

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.enter_set.remove(self.identifier)
        self.exit_set.add(self.identifier)
        logging.debug(f"Exit  message: {self.identifier}")


class AutoLockMultiprocessingDefaultdict:
    """
    Multiprocessing compatible dict
    """
    def __init__(self, data_type, mgr):
        self._dict = mgr.defaultdict(data_type)
        self._lock = mgr.Lock()

    def __getitem__(self, k):
        with self._lock:
            return self._dict[k]

    def __setitem__(self, k, v):
        with self._lock:
            self._dict[k] = v

    def __str__(self):
        with self._lock:
            return str(self._dict)


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

