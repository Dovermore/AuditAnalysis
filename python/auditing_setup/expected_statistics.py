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

from auditing_setup.raw_distributions import AuditMethodDistributionComputer, to_csv
from auditing_setup.audit_methods import Bayesian, BRAVO, make_legend

from os.path import join

import numpy as np


class ExpectedStatisticsComputer:
    def __init__(self, audit_class, n, m, replacement=False):
        self.n = n
        if m == -1:
            m = n
        self.m = m
        self.audit_class = audit_class
        self.replacement = replacement

    def compute_statistics(self, true_p, *args, **kwargs):
        audit_simulation = AuditMethodDistributionComputer(self.audit_class, self.n,
                                                           self.m, self.replacement)
        power, dsample_power = audit_simulation.power(true_p, dsample=True, *args, **kwargs)
        m = max(dsample_power.keys())
        statistics_power = self.extract_statistics(dsample_power, self.n, m)

        audit_simulation = AuditMethodDistributionComputer(self.audit_class, self.n,
                                                           m, self.replacement)

        risk, dsample_risk = audit_simulation.power(0.5, dsample=True, *args, **kwargs)
        statistics_risk = self.extract_statistics(dsample_risk, self.n, m)

        # TODO change name for power to alt and add separation sign
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
        key, params = AuditMethodDistributionComputer._parse_params(params)
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
    def extract_statistics(dsample, n, m):
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
                ExpectedStatisticsComputer.\
                    update_quantile(t, cumulative_probability,
                                    quantile, statistics)
            if t >= m:
                break
        # Update mean by computing (computed mean + rest prob * m)
        statistics["mean"] = mean
        statistics["mean_with_recount"] = mean + (1 - cumulative_probability) * (m+n)
        # The rest of the statistics should be 1
        cumulative_probability = 1
        for quantile in quantiles:
            ExpectedStatisticsComputer.\
                update_quantile(m, cumulative_probability, quantile,
                                statistics)
        return statistics


def audit_method_expected_statistics(audit_method, audit_params, n, m, true_ps=np.linspace(0.45, 0.75, 25),
                                     save=False, fpath="data"):
    expected_statistics_computer = ExpectedStatisticsComputer(audit_method, n, m, False)

    statistics_dfs = dd(lambda: pd.DataFrame())
    for params in audit_params:
        print("param:", params)
        legend = make_legend(audit_method, **params)
        statistics_data = dd(lambda: {"legend": legend})
        for true_p in true_ps:
            print("    true_p:", true_p)
            statistics = expected_statistics_computer.compute_statistics(true_p, **params)
            for stat_type in statistics.index:
                statistics_data[stat_type][true_p] = statistics[stat_type]
        for stat_type in statistics_data:
            statistics_dfs[stat_type] = statistics_dfs[stat_type].append(statistics_data[stat_type], ignore_index=True)
    for stat_type in statistics_dfs:
        statistics_dfs[stat_type] = statistics_dfs[stat_type].set_index("legend")
    if save:
        for stat_type in statistics_dfs:
            to_csv(statistics_dfs[stat_type], f"{audit_method.name}_{stat_type}.csv", fpath)
    return statistics_dfs


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
    sss = ExpectedStatisticsComputer(audit_method, 5000, 0.9, False)
    summary = None
    if test_mode == 0:
        summary = sss.compute_statistics(0.6, thresh=0.95, *args, **kwargs)
    elif test_mode == 1:
        summary = sss.compute_param_dict_statistics(0.7, param_dict,
                                                    *args, **kwargs)
    print(summary)



