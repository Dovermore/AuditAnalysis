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
    def __init__(self, audit_class, n, m, step=1, replacement=False):
        """
        Instantiate a new computer for a certain election setup
        :param audit_class: The class of audit to use
        :param n: total number of ballots
        :param m: number to sample
        :param step: number to sample each timestamp
        :param replacement: sampling with or without replacement?
        """
        self.n = n
        if m == -1:
            m = n
        self.m = m
        # TODO refactor this parameter to compute_statistics
        self.audit_class = audit_class
        self.step = step
        self.replacement = replacement

    def compute_statistics(self, true_p, return_pdf=False, *args, **kwargs):
        audit_simulation = AuditMethodDistributionComputer(self.audit_class, self.n,
                                                           self.m, step=self.step, replacement=self.replacement)

        # Computer all statistics related to alternative hypothesis
        power, dsample_power = audit_simulation.power(true_p, dsample=True, *args, **kwargs)
        statistics_power = self.extract_statistics(dsample_power, self.n, self.m, power)
        summary_statistics = dict()
        summary_statistics["power"] = power
        summary_statistics.update({key: statistics_power[key] for key in statistics_power})
        summary_statistics = pd.Series(summary_statistics, name=self.m)
        if return_pdf:
            return summary_statistics, dsample_power
        return summary_statistics

    def compute_param_dict_statistics(self, true_p, params, *args, **kwargs):
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
    def update_quantile(t, cumulative_probability, quantile, statistics, prefix="unconditional"):
        entry = f"{prefix}_quantile{quantile:.2f}"
        if cumulative_probability >= quantile and entry \
                not in statistics:
            statistics[entry] = t

    @staticmethod
    def extract_statistics(dsample, n, m, power, quantiles=(0.25, 0.5, 0.75, 0.9, 0.99)):
        """
        :param dsample: Dictionary or pd.Series of distribution of sample
        :param n: The election size
        :param m: The max number sampled (To compute mean)
        :param power: the power of the dsample (not necessary but to reduce the amount of computation)
        :param quantiles: the quantiles to get statistics from
        :return: pd.Series of computed statistics
        """
        dsample = pd.Series(dsample)
        statistics = dd(float)
        cumulative_probability = 0
        unconditional_mean = 0
        for t in sorted(dsample.index):
            cumulative_probability += dsample[t]
            unconditional_mean += dsample[t] * t
            for quantile in quantiles:
                # Update unconditional quantile
                ExpectedStatisticsComputer.update_quantile(t, cumulative_probability, quantile, statistics)
                # Update conditional quantile
                ExpectedStatisticsComputer.update_quantile(t, cumulative_probability/power, quantile, statistics,
                                                           prefix="conditional")
            if t >= m:
                break

        # Update mean by computing (computed mean + rest prob * m)
        statistics["unconditional_mean"] = unconditional_mean + (1 - cumulative_probability) * m
        statistics["unconditional_mean_with_recount"] = unconditional_mean + (1 - cumulative_probability) * (m+n)
        statistics["conditional_mean"] = unconditional_mean / power

        # The rest of the statistics should be 1
        cumulative_probability = 1
        for quantile in quantiles:
            ExpectedStatisticsComputer.update_quantile(m, cumulative_probability, quantile, statistics)
        return statistics


def audit_method_expected_statistics(audit_method, audit_params, n, m, true_ps=np.linspace(0.45, 0.75, 25),
                                     step=1, replacement=False, save=False, fpath="data", include_risk=True):
    true_ps = list(true_ps)
    expected_statistics_computer = ExpectedStatisticsComputer(audit_method, n, m, step=step, replacement=replacement)

    # Store all statistics in a dictionary of DataFrame with values of same type of statistics
    statistics_dfs = dd(lambda: pd.DataFrame())
    legends = []
    pdf_dfs = []
    cdf_dfs = []
    for params in audit_params:
        legend = make_legend(audit_method, **params)
        legends.append(legend)

        # Made up of each type of statistics and each row of data in statistics_df (for all p)
        statistics_data = dd(lambda: {"legend": legend})
        # Store all pdf data and cdf data
        pdf_data = []
        cdf_data = []

        # add 0.5 for computing risk as well.
        if include_risk:
            true_ps.insert(0, 0.5)
        for true_p in true_ps:
            print("    true_p:", true_p)
            statistics, pdf = expected_statistics_computer.compute_statistics(true_p, return_pdf=True, **params)
            cdf = AuditMethodDistributionComputer.dsample_to_cdf(pdf, m)

            for stat_type in statistics.index:
                statistics_data[stat_type][true_p] = statistics[stat_type]
            pdf_data.append(pdf)
            cdf_data.append(cdf)

        for stat_type in statistics_data:
            statistics_dfs[stat_type] = statistics_dfs[stat_type].append(statistics_data[stat_type], ignore_index=True)

        pdf_data = pd.concat(pdf_data, axis=1)
        pdf_data = pdf_data.fillna(value=0)
        pdf_data.columns = true_ps
        pdf_dfs.append(pdf_data)

        cdf_data = pd.concat(cdf_data, axis=1)
        cdf_data = cdf_data.fillna(value=0)
        cdf_data.columns = true_ps
        cdf_dfs.append(cdf_data)

    for stat_type in statistics_dfs:
        statistics_dfs[stat_type] = statistics_dfs[stat_type].set_index("legend")

    pdf_dfs = pd.concat(pdf_dfs, keys=legends)
    cdf_dfs = pd.concat(cdf_dfs, keys=legends)
    statistics_dfs["pdf"] = pdf_dfs
    statistics_dfs["cdf"] = cdf_dfs
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



