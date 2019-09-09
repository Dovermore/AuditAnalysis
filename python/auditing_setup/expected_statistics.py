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
from auditing_setup.election_setting import Election
from typing import List

from os.path import join

import numpy as np


class ExpectedStatisticsComputer:
    def __init__(self, audit_class):
        """
        Instantiate a new computer for a certain election setup
        :param audit_class: The class of audit to use
        """
        self.audit_class = audit_class

    def compute_statistics(self, election: Election, return_pdf=False, *args, **kwargs):
        audit_simulation = AuditMethodDistributionComputer(self.audit_class)

        # Computer all statistics related to alternative hypothesis
        power, dsample_power = audit_simulation.power(election, dsample=True, *args, **kwargs)
        statistics_power = self.extract_statistics(dsample_power, election)
        summary_statistics = dict()
        summary_statistics["power"] = power
        summary_statistics.update({key: statistics_power[key] for key in statistics_power})
        summary_statistics = pd.Series(summary_statistics, name=election.m)
        if return_pdf:
            return summary_statistics, dsample_power
        return summary_statistics

    def compute_param_dict_statistics(self, election: Election, param_dict, *args, **kwargs):
        key, params = AuditMethodDistributionComputer._parse_params(param_dict)
        all_statistics = pd.DataFrame()
        for param in params:
            print(f"            param = {param}")
            kwargs[key] = param
            summary_statistics = self.compute_statistics(election, *args, **kwargs)
            all_statistics = all_statistics.append(summary_statistics, ignore_index=True)
        return all_statistics

    @staticmethod
    def update_quantile(t, cumulative_probability, quantile, statistics, prefix="unconditional"):
        entry = f"{prefix}_quantile{quantile:.2f}"
        if cumulative_probability >= quantile and entry \
                not in statistics:
            statistics[entry] = t

    @staticmethod
    def extract_statistics(dsample, election:Election, quantiles=(0.25, 0.5, 0.75, 0.9, 0.99)):
        """
        :param dsample: Dictionary or pd.Series of distribution of sample
        :param quantiles: the quantiles to get statistics from
        :return: pd.Series of computed statistics
        """
        power = sum(dsample.values)
        n = election.n
        m = election.m

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


def audit_method_expected_statistics(audit_method, audit_params, elections: List[Election], fpath="data"):
    true_ps = [election.p for election in elections]
    expected_statistics_computer = ExpectedStatisticsComputer(audit_method)

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

        for true_p, election in zip(true_ps, elections):
            print("    true_p:", true_p)
            statistics, pdf = expected_statistics_computer.compute_statistics(election, return_pdf=True, **params)
            cdf = AuditMethodDistributionComputer.dsample_to_cdf(pdf, election.m)

            for stat_type in statistics.index:
                statistics_data[stat_type][election.p] = statistics[stat_type]
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
    if fpath is not None:
        for stat_type in statistics_dfs:
            to_csv(statistics_dfs[stat_type], f"{audit_method.name}_{stat_type}.csv", fpath)
    return statistics_dfs

