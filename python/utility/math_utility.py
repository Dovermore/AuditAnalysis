import numpy as np

from utility.program_utility import Cached

# rpy2 use r in python
from rpy2.robjects.packages import importr
from rpy2.robjects import r

# import R's "base" package
base = importr('base')
# import R's "utils" package
utils = importr('utils')
hypergeo = importr("hypergeo")
vgam = importr("VGAM")
extra_distr = importr("extraDistr")


def addln(aln, bln):
    """
    Add two log numbers together
    ln(a+b) = ln(a*(1+b/a)) = ln(a) + ln(1+b/a) = ln(a) + ln(1+e^(ln(b)-ln(a)))
    """
    maxln = max(aln, bln)
    minln = min(aln, bln)

    return maxln + np.log(1 + np.exp(minln-maxln))


@Cached
def beta_binomial_cdf(k, a, b, n, method="normal", library="extraDistr"):
    """
    Computes the posterior cdf for a beta-binomial distribution

    Args:
        k (int): this function computes (P(S <= k))
        a (float): Alpha prior placed on one winner side
        b(float): Beta prior placed on the loser side
        n (int): Total number of votes to simulate
        method (string): The method which the function computes the
                probability and return with
        library (string): R package to use for computation
    """
    if k >= n:
        return 1
    if k < 0:
        return 0

    log = True if method == "log" else False
    if library == "vgam":
        prob = list(vgam.pbetabinom_ab(k, n, a, b, log_p=log))[0]
    elif library == "extraDistr":
        prob = list(extra_distr.pbbinom(k, n, a, b, log_p=log))[0]
    else:
        assert 0
    return prob


@Cached
def beta_binomial_pmf(k, a, b, n):
    return list(vgam.dbetabinom_ab(k, n, a, b))[0]


@Cached
def beta_pdf(x, a, b, log):
    return r.dbeta(x, a, b, log=log)


@Cached
def betafn(a, b, log=False):
    """
    Ported r beta function that integrates lbeta and beta together
    :param a: alpha
    :param b: beta
    :param log: log output
    """
    if log:
        return list(r.lbeta(a, b))[0]
    return list(r.beta(a, b))[0]


@Cached
def beta_cdf(p, a, b, log=False, lower_tail=True):
    return list(r.pbeta(p, a, b, log_p=log, lower_tail=lower_tail))[0]


@Cached
def hypergeom_pmf(k, M, n, N, log=False):
    """
    From r api to scipy api
    log to indicate whether to use log output
    """
    return list(r.dhyper(k, n, M-n, N, log=log))[0]


@Cached
def binom_pmf(k, n, p, log=False):
    return list(r.dbinom(k, n, p, log=log))[0]
