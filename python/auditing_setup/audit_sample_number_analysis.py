# TODO --90%--
"""
This file aims to generate the following type of data:

1.
    for a set of given true underlying distribution, find the amount of votes
    needed to have x% of power (90% ideally, but for closer margin I will
    shrink this considerably, this also depends on the methodology)

2.
    After finding the required amount of votes, find out the corresponding
    type 1 error rate for the sample number.

3.
    It's very intimidating to find alpha for such case, but it's very hard to
    do so.
"""

import pandas as pd
from collections import defaultdict as dd

from auditing_setup.audit_power import AuditSimulation
from auditing_setup.audit_method import Bayesian, BRAVO

import numpy as np


class SampleStatisticsSimulation:
    def __init__(self, audit_class, n, m, replacement=False):
        self.n = n
        if m == -1:
            m = n
        self.m = m
        self.audit_class = audit_class
        self.replacement = replacement

    def compute_statistics(self, true_p, *args, **kwargs):
        audit_simulation = AuditSimulation(self.audit_class, self.n,
                                           self.m, self.replacement)
        power, dsample_power = audit_simulation.power(true_p, dsample=True, *args, **kwargs)
        m = max(dsample_power.keys())
        statistics_power = self.extract_statistics(dsample_power, m)

        audit_simulation = AuditSimulation(self.audit_class, self.n,
                                           m, self.replacement)

        risk, dsample_risk = audit_simulation.power\
            (0.5, dsample=True, *args, **kwargs)
        statistics_risk = self.extract_statistics(dsample_risk, m)

        summary_statistics = dict()
        summary_statistics["power"] = power
        summary_statistics.update({f"power{key}": statistics_power[key]
                                   for key in statistics_power})
        summary_statistics["risk"] = risk
        summary_statistics.update({f"risk{key}": statistics_risk[key]
                                   for key in statistics_risk})
        summary_statistics = pd.Series(summary_statistics, name=m)
        return summary_statistics

    def compute_param_dict_statistics(self, true_p, params, *args,
                                      **kwargs):
        key, params = AuditSimulation._parse_params(params)
        all_statistics = pd.DataFrame()
        for param in params:
            print(f"            param = {param}")
            kwargs[key] = param
            summary_statistics = self.compute_statistics(true_p, *args,
                                                         **kwargs)
            all_statistics = \
                all_statistics.append(summary_statistics, ignore_index=True)
        return all_statistics

    @staticmethod
    def update_quantile(t, cumulative_probability, quantile, statistics):
        entry = f">={quantile:.2f}"
        if cumulative_probability >= quantile and entry \
                not in statistics:
            statistics[entry] = t

    @staticmethod
    def extract_statistics(dsample, m):
        """
        :param dsample: Dictionary or pd.Series of distribution of sample
        :param m: The max number sampled (To compute mean)
        :return: pd.Series of computed statistics
        """
        dsample = pd.Series(dsample)
        statistics = dd(float)
        cumulative_probability = 0

        quantiles = [0.25, 0.5, 0.75, 0.9]
        mean = 0
        for t in sorted(dsample.index):
            cumulative_probability += dsample[t]
            mean += dsample[t] * t
            for quantile in quantiles:
                SampleStatisticsSimulation.\
                    update_quantile(t, cumulative_probability,
                                    quantile, statistics)
            if t >= m:
                break
        # Update mean by computing (computed mean + rest prob * m)
        statistics["mean"] = mean
        statistics["mean_with_full_count"] = mean + (1 - cumulative_probability) * m
        # The rest of the statistics should be 1
        cumulative_probability = 1
        for quantile in quantiles:
            SampleStatisticsSimulation.\
                update_quantile(m, cumulative_probability, quantile,
                                statistics)
        return statistics


if __name__ == "__main__":
    test_mode = 1
    audit_method = BRAVO
    args = []
    kwargs = {}
    param_dict = {}
    if audit_method is Bayesian:
        param_dict = {"thresh": list(np.linspace(0.95, 0.99, 10))}
    elif audit_method is BRAVO:
        kwargs["p"] = 0.6
        param_dict = {"alpha": list(np.linspace(0.01, 0.20, 20))}
    sss = SampleStatisticsSimulation(audit_method, 5000, 0.9, False)
    summary = None
    if test_mode == 0:
        summary = sss.compute_statistics(0.6, thresh=0.95, *args, **kwargs)
    elif test_mode == 1:
        summary = sss.compute_param_dict_statistics(0.7, param_dict,
                                                    *args, **kwargs)
    print(summary)



