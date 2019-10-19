from utility.program_utility import CachedMethod, string_to_num, memoized_method
from utility.math_utility import beta_binomial_cdf, beta_pdf, betafn, beta_cdf, hypergeom_pmf, addln
from auditing_setup.election_setting import Election
from math import ceil, log, isinf, exp
import pandas as pd
import numpy as np
from scipy.stats import norm, hypergeom
from rpy2.robjects.packages import importr
import abc
import logging


sequential = importr("Sequential")

console_logger = logging.getLogger("console_logger")


class BaseMethod(abc.ABC):
    name = "base_name"
    critical_attributes = []

    def __init__(self, election: Election = None, min_stop=False):
        self.min_stop = min_stop
        self.election = election

    def __call__(self, n, t, y_t):
        return False

    def __str__(self):
        attributes = []
        for key in self.critical_attributes:
            attribute = "{}".format(key)
            value = self.__dict__[key]
            if isinstance(value, int):
                attribute += "={:02}".format(value)
            elif isinstance(value, float):
                attribute += "={:.3f}".format(value)
            else:
                attribute += "={}".format(value)
            attributes.append(attribute)
        attributes.insert(0, self.name)
        return "_".join(attributes)

    @classmethod
    def legend(cls, *args, **kwargs):
        return str(cls.__init__(*args, **kwargs))

    def min_stop_check(self, t):
        return self.min_stop is not False and t < self.min_stop


class BayesianMethod(BaseMethod, abc.ABC):
    name = "bayesian_method"
    critical_attributes = ["a", "b", "critical_value"]

    def __init__(self, a=1, b=1, critical_value=0.05, *args, **kwargs):
        super(BayesianMethod, self).__init__(*args, **kwargs)
        self.a = a
        self.b = b
        self.critical_value = critical_value

    def compute_upset_prob(self, n, t, y_t):
        return 1

    def __call__(self, n, t, y_t):
        if self.min_stop_check(t):
            return False
        return self.compute_upset_prob(n, t, y_t) < self.critical_value


class FrequentistMethod(BaseMethod, abc.ABC):
    name = "frequentist_method"
    critical_attributes = ["alpha"]

    def __init__(self, alpha, *args, **kwargs):
        super(FrequentistMethod, self).__init__(*args, **kwargs)
        self.alpha = alpha


class Bayesian(BayesianMethod):
    name = "bayesian"

    def __init__(self, a=1, b=1, critical_value=0.05,  min_stop=False, *args, **kwargs):
        super(Bayesian, self).__init__(a=a, b=b, critical_value=critical_value, min_stop=min_stop, *args, **kwargs)

    @memoized_method(maxsize=250)
    def compute_upset_prob(self, n, t, y_t):
        k = ceil(n/2 - y_t)
        upset_prob = beta_binomial_cdf(k, y_t+self.a, t-y_t+self.b, n-t)
        return upset_prob


class BetaBayesian(BayesianMethod):
    name = "bayesian_with_replacement"

    @memoized_method(maxsize=250)
    def compute_upset_prob(self, n, t, y_t):
        # prior      p   ~ beta(a, b)
        # likelihood x|p ~ bi(t, p)
        # posterior  p|x ~ beta(a+y_t, b+t-y_t)
        # Upset prob p(p|x <= 0.5)

        # This is the upset_prob according to the above formulation
        return beta_cdf(0.5, self.a+y_t, self.b+t-y_t, lower_tail=True)


class TruncatedBayesian(BayesianMethod):
    name = "truncated_bayesian"

    def __init__(self, critical_value=0.05, p_0=0.5, a=1, b=1, min_stop=False, *args, **kwargs):
        super(TruncatedBayesian, self).__init__(a=a, b=b, critical_value=critical_value,
                                                min_stop=min_stop, *args, **kwargs)
        self.p_0 = p_0

    @memoized_method(maxsize=250)
    def compute_upset_prob(self, n, t, y_t):
        betalnfn_ratio = betafn(y_t + self.a, t - y_t + self.b, log=True) - betafn(self.a, self.b, log=True)
        # betafn_ratio = exp(betalnfn_ratio)
        betadistln_ratio = (beta_cdf(1/2, y_t + self.a, t - y_t + self.b, log=True, lower_tail=False)
                            - beta_cdf(1/2, self.a, self.b, log=True, lower_tail=False))
        # betadist_ratio = (beta_cdf(1/2, y_t + self.a, t - y_t + self.b, lower_tail=False)
        #                   / beta_cdf(1/2, self.a, self.b, lower_tail=False))
        right = log(1/2) + betalnfn_ratio + betadistln_ratio
        left = -(t+1) * log(2)
        k_primeln = addln(left, right)
        # k_prime = 1/(2**(t+1)) + 1/2 * betafn_ratio * betadist_ratio
        # upset_prob = (1/(2**(t+1))) / k_prime
        # No log transformation
        upset_probln = -(t+1) * log(2) - k_primeln
        return exp(upset_probln)


class SPRTMethod(FrequentistMethod):
    name = "sprt"
    critical_attributes = ["alpha", "p"]

    def __init__(self, alpha, p, p_0=0.5, *args, **kwargs):
        super(SPRTMethod, self).__init__(alpha=alpha, *args, **kwargs)
        self.p = p
        self.p_0 = p_0
        self.critical_value = log(1/alpha)


# BRAVO
class BRAVO(SPRTMethod):
    name = "bravo"

    def __init__(self, p, alpha, p_0=0.5, *args, **kwargs):
        """
        :param p: The assumed true share
        :param alpha: The risk limit
        :param p_0: p_0 used for null hypothesis (default to 0.5)
        """
        super(BRAVO, self).__init__(alpha=alpha, p=p, p_0=p_0, *args, **kwargs)
        self.y_val = log(p/p_0)
        self.not_y_val = log((1-p)/(1-p_0))

    @memoized_method(maxsize=250)
    def __call__(self, n, t, y_t):
        if self.min_stop_check(t):
            return False
        y = y_t
        not_y = t - y
        
        # log(p/0.5)^y
        sum_y_val = self.y_val * y
        # log((1-p)/0.5)^(t-y)
        sum_not_y_val = self.not_y_val * not_y
        
        # total log(p/0.5)^y + log((1-p)/0.5)^(t-y) = log()
        sum_val = sum_y_val + sum_not_y_val
        return sum_val >= self.critical_value


# BRAVO
class HyperGeomBRAVO(SPRTMethod):
    name = "bravo_without_replacement"

    @memoized_method(maxsize=250)
    def __call__(self, n, t, y_t):
        if self.min_stop_check(t):
            return False
        y = y_t
        not_y = t - y

        # The amount for winner under alternative
        p1N = int(n * self.p)
        # The amount for winner under null
        p0N = int(n * self.p_0)

        # The amount for winner is greater than alternative
        if y >= p1N:
            return True
        # The amount for loser is greater than votes in null hypothesis for loser
        elif not_y >= n - p0N:
            return False

        # log(top)
        log_prob_p1 = hypergeom_pmf(y, n, p1N, t, log=True)
        # log(bot)
        log_prob_p0 = hypergeom_pmf(y, n, p0N, t, log=True)

        inf_p0 = isinf(log_prob_p0)
        inf_p1 = isinf(log_prob_p1)
        # Both return null, means the chance is in between
        if inf_p0 and inf_p1:
            #
            if y > p0N:
                return True
            return False
        # Chance for null is zero
        elif inf_p0:
            return True
        # Chance for alternative is zero
        elif inf_p1:
            return False

        # total log(top) - log(bottom)
        ratio = log_prob_p1 - log_prob_p0

        # print(n, t, y_t, log_prob_p0, log_prob_p1, ratio, self.critical_value)
        return ratio >= self.critical_value


class Clip(FrequentistMethod):
    name = "clip"

    betas = pd.DataFrame(
        [
            [2.683, 2.500, 2.236, 2.000, 1.732, 1.155],
            [2.887, 2.694, 2.425, 2.145, 1.877, 1.343],
            [3.054, 2.864, 2.546, 2.294, 2.000, 1.414],
            [3.184, 3.000, 2.670, 2.401, 2.095, 1.511],
            [3.290, 3.077, 2.770, 2.496, 2.183, 1.633],
            [3.357, 3.144, 2.828, 2.556, 2.240, 1.715],
            [3.411, 3.206, 2.889, 2.638, 2.324, 1.747],
            [3.487, 3.273, 2.958, 2.684, 2.375, 1.817],
            [3.530, 3.309, 3.000, 2.734, 2.438, 1.890],
            [3.560, 3.352, 3.040, 2.782, 2.474, 1.937]
        ],
        columns=[0.01, 0.02, 0.05, 0.1, 0.2, 0.5],
        index=[100, 300, 1000, 3000, 10000, 30000, 100000, 300000,
               1000000, 3000000])

    @staticmethod
    def _compute_beta(n, alpha, conservative=False):
        """
        Approximate compute beta based on values
        """
        if conservative:
            const = 1
        else:
            const = 0.86
        return 0.075 * np.log(n) + 0.7 * norm.isf(alpha) + const

    def __init__(self, alpha, conservative=False, *args, **kwargs):
        super().__init__(alpha=alpha, *args, **kwargs)
        self.n = self.election.n
        if self.n in self.betas.index and alpha in self.betas.columns:
            self.beta = self.betas.loc[self.n, alpha]
        else:
            self.beta = self._compute_beta(self.n, alpha, conservative)

    @memoized_method(maxsize=250)
    def __call__(self, n, t, y_t):
        if self.min_stop_check(t):
            return False
        a = y_t
        b = t - y_t
        return (a - b) > self.beta * np.sqrt(t)


class MaxSPRT(FrequentistMethod):
    name = "max_sprt"

    def __init__(self, alpha, auto_max_sample=None, p_0=0.5, min_rejection=1, *args, **kwargs):
        """
        :param alpha: The risk limit
        :param p_0: p_0 used for null hypothesis (default to 0.5)
        """
        super().__init__(alpha=alpha, *args, **kwargs)
        self.p_0 = p_0
        self.max_sample = auto_max_sample

        if auto_max_sample is None:
            self.critical_value = log(1/alpha)
        else:
            self.critical_value = sequential.CV_Binomial(auto_max_sample, alpha, min_rejection, p=p_0)[0][0]

    @memoized_method(maxsize=250)
    def __call__(self, n, t, y_t):
        if self.min_stop_check(t):
            return False
        # print("|", n, t, y_t, "|")
        y = y_t
        not_y = t - y

        p_0 = self.p_0
        # Assumes the alternative is p > p_0
        p_mle = max(p_0, y_t / t)

        y_val = log(p_mle/p_0)
        not_y_val = log((1-p_mle)/(1-p_0)) if not_y else 0

        # y * log(p_mle/0.5)
        sum_y_val = y_val * y

        # (t-y) * log((1-p_mle)/0.5)
        sum_not_y_val = not_y_val * not_y

        # total log(p/0.5)^y + log((1-p)/0.5)^(t-y)
        sum_val = sum_y_val + sum_not_y_val

        return sum_val >= self.critical_value


def make_legend(audit_method, for_file=False, **kwargs):
    legend = "{:8}".format(audit_method.name)
    split = " | "
    if for_file:
        split = "_"
    for key, value in kwargs.items():
        legend += "{}{}={}".format(split, key, value)
    return legend
