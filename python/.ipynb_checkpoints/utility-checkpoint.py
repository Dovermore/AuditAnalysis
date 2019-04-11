import mpmath as mm
from math import ceil
import numpy as np

from scipy.stats import binom
from scipy.special import beta as beta
from scipy.special import betaln
from scipy.special import comb
from scipy.special import gammaln

from collections import defaultdict as dd
from collections import deque
from functools import partial

import sys

# rpy2 use r in python
from rpy2.robjects.packages import importr

# import R's "base" package
base = importr('base')
# import R's "utils" package
utils = importr('utils')
hypergeo = importr("hypergeo")
rmutil = importr("rmutil")
tail_rank = importr("TailRank")


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
            ret = self.cache[(args, sorted_kwargs)] = self.function(*args,
                                                                    **kwargs)
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
        self._dict = dd(float)
        
    def append(self, key, value):
        # Didn't find
        if key not in self._q:
            self._q.appendleft(key)
            self._dict[key] = value
        else:
            self._dict[key] += value
        
    def pop(self):
        key = self._q.pop()
        value = self._dict[key]
        del self._dict[key]
        return key, value

    def peek(self):
        key = self._q[-1]
        value = self._dict[key]
        return key, value
    
    def __repr__(self):
        return str([(key, self._dict[key]) for key in self._q])
    
    def serialize(self):
        return [(key, self._dict[key]) for key in self._q]
    

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


def combln(n, k):
    return gammaln(n + 1) - gammaln(n - k + 1) - gammaln(k + 1)


def addln(aln, bln):
    """
    Add two log numbers together
    ln(a+b) = ln(a*(1+b/a)) = ln(a) + ln(1+b/a) = ln(a) + ln(1+e^(ln(b)-ln(a)))
    """
    maxln = max(aln, bln)
    minln = min(aln, bln)
    
    return maxln + np.log(1 + np.exp(minln-maxln))


def beta_binomial_cdf(k, a, b, n, definition="r", method="normal"):
    """
    Computes the posterior cdf for a beta-binomial distribution
    
    Args:
        k (int): this function computes (P(S <= k))
        a (float): Alpha prior placed on one winner side
        b(float): Beta prior placed on the loser side
        n (int): Total number of votes to simulate
        definition (string): The implementation to use (Currently
                only wolfram definition is working correctly)
        method (string): The method which the function computes the
                probability and return with
    """
       
    if k >= n:
        return 1
    if k < 0:
        return 0
    
    if definition == "wiki":
        print("Wiki method is still not working correctly", file=sys.stderr)
        c_nk = comb(n, k)
        bb = beta(k+a, n-k+b) / beta(a, b)
        geom = mm.hyp3f2(1, -k, n-k+b, n-k-1, 1-k-a, 1)
        return c_nk * bb * geom
    elif definition == "wolfram":
        if method == "normal":
            bb = beta(b+n-k-1, a+k+1) / beta(a, b) / beta(n-k, k+2)
            geom = mm.hyp3f2(1, a+k+1, -n+k+1, k+2, -b-n+k+2, 1)
            gam = 1 / (n+1) / (n+2)
            prob = 1 - n * bb * geom * gam
        elif method == "log":
            bbln = betaln(b+n-k-1, a+k+1) - betaln(a, b) - betaln(n-k, k+2)
            geomln = np.log(mm.hyp3f2(1, a+k+1, -n+k+1, k+2, -b-n+k+2, 1))
            gamln = gammaln(n) - gammaln(n+2)
            prob = addln(np.log(1), -(np.log(n) + bbln + geomln + gamln))
        else:
            print("Invalid method", file=sys.stderr)
            return
    elif definition == "r":
        if method == "normal":
            prob = list(tail_rank.pbb(k, n, a, b))[0]
        elif method == "log":
            prob = np.log(list(tail_rank.pbb(k, n, a, b))[0])
        else:
            print("Invalid method", file=sys.stderr)
            return
    else:
        print("Invalid definition", file=sys.stderr)
        return
    return prob
            

def _single_posterior_pmf(sa, s, n, a=1, b=1, thresh=0.95,
                          p_h0=1/2, verbose=False, full_return=False,
                          *args, **kwargs):
    """
    This function calculate the one part of posterior probability of
    rejecting the null hypothesis when null hypothesis is true with 
    given sampled S_A from a set of samples of size S of an election 
    of size N. The prior is given by alpha and beta where alpha denotes 
    the number of additional votes to the winner and the beta denotes 
    the additional votes to loser.
    
    Args:
        sa (int): number of votes out of S the winner A got
        s (int): total number of votes sampled
        n (int): size of election
        a (float/int): prior denoting additional votes to winner A
        b (float/int): prior denoting additional votes to loser B
        thresh (float,[0, 1]): the threshold rejecting null hypothesis
        p_ho (float, default 0.5): the null hypothesis
    Returns:
        p(sa) if NULL is rejected else 0
    """
    # Try compute with/without celling
    # k = n/2 - sa
    k = ceil(n/2 - sa)
    p_reject = 1 - beta_binomial_cdf(k, sa+a, s-sa+b, n-s, *args, **kwargs)
    if verbose:
        pretty_print(sa=(sa, 6), s=(s, 6), n=(n, 6), alpha=(a, 6),
                     beta=(b, 6), rejection_proba=(float(p_reject), 20,
                                                   "20.4f"),
                     binomial_proba=(binom.pmf(sa, s, p_h0), 20, "20.4f"))
        verbose -= 1
    if full_return:
        return binom.pmf(sa, s, p_h0), p_reject
    return binom.pmf(sa, s, p_h0) if p_reject >= thresh else 0


def posterior_pmf(s, n, a=1, b=1, thresh=0.95, p_h0=1/2, 
                  verbose=False, full_return=False,
                  *args, **kwargs):
    """
    Args:
        s (int): number of sampled votes
        n (int): total votes in the election
        a (float): prior alpha for the winner
        b (float): prior beta for the winner
        thresh (0 < ` < 1): threshold over which the null is rejected
        p_h0 (0 < ` < 1): the null hypothesis to test with
        verbose: verbocity of the output, level 0 to 2
                 (2 must be used with full_return)
        full_return: if the return should be full list of
                     individual probabilities
    """
    p = 0
    ps = []
    if full_return:
        for sa in range(0, s+1):
            p_binomial, p_reject = \
                _single_posterior_pmf(sa, s, n, a, b, thresh, p_h0,
                                      verbose - 1 if verbose else verbose,
                                      full_return=True, *args, **kwargs)
            p += p_binomial * (p_reject >= thresh)
            ps.append([p_binomial, p_reject])
    else:
        sa = 0
        # Find the first value it starts to give positive number
        k = ceil(n/2 - sa)
        while 1 - beta_binomial_cdf(k, sa+a, s-sa+b, n-s, 
                                    *args, **kwargs) < thresh and sa <= s:
            sa += 1
            k = ceil(n/2 - sa)
        # The value of sa now is the threshold
        if sa <= s:
            p = 1 - binom.cdf(sa-1, s, p_h0)
        
    if verbose:
        pretty_print(s=(s, 6), n=(n, 6), alpha=(a, 6), beta=(b, 6),
                     overall=(p, 20, "20.4f"), sep=2)
    if full_return:
        return p, ps
    return p


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
