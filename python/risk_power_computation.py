from audit_method import Bayesian, BRAVO, Clip
from stochastic_simulation import stochastic_process_simulation
from collections import defaultdict as dd
from math import ceil
from os import makedirs
from os.path import exists, join

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


class AuditSimulation:
    def __init__(self, audit_class, n, m):
        self.n = n
        self.m = m
        self.audit_class = audit_class

    def power(self, true_p, progression=False, dsample=False, *args, **kwargs):
        """
        Mostly used as helper for computing a single power
        :param true_p: The true proportion of winner's share
        :param progression: If a progression bar should be used
        :param dsample: distribution of sample votes
        :param args: Parameters supporting the creation of auditing function
        :param kwargs: Parameters supporting the creation of auditing function
        :return: The power of current simulation
        """
        audit_f = self.audit_class(*args, **kwargs)
        reject_dict = \
            stochastic_process_simulation(audit_f, n=self.n,
                                          m=self.m, p=true_p,
                                          progression=progression)
        power = sum(reject_dict.values())
        ret = power
        if dsample:
            dsample = dd(float)
            for key in reject_dict:
                t, y_t = key
                proba = reject_dict[key]
                dsample[t] += proba
            ret = [power, pd.Series(dsample).sort_values(axis="index")]
        return ret

    @staticmethod
    def _parse_params(params):
        key = None
        for key in params:
            break
        return key, params[key]

    def powers(self, true_p, params, dsample=False, *args, **kwargs):
        """
        Compute set of powers for a set of parameters, will return a
        pandas.Series as result
        :param true_p: The true proportion of winner's share
        :param params: single {key: values} pair of parameters to be simulated
        :param args: Other supportive arguments
        :param kwargs: Other supportive arguments
        :return: pd.Series of all simulated results.
        """
        key, params = self._parse_params(params)
        if dsample:
            dsamples = pd.DataFrame(columns=params)
        simulations = {}
        for param in params:
            kwargs[key] = param
            power = self.power(true_p, progression=False, dsample=dsample,
                             *args, **kwargs)
            if dsample:
                power, _dsample = power
                dsamples[param] = _dsample
            simulations[param] = power
        ret = pd.Series(simulations, name=key)
        if dsample:
            ret = [ret, dsamples]
        return ret

    def tabular_power(self, true_ps, params, dsample=False, *args, **kwargs):
        """
        Compute table of powers for a set of parameters, and a set of true
        probabilities will return a pandas.DataFrame as result
        :param true_ps: List of true proportions of winner's share
        :param params: single {key: values} pair of parameters to be simulated
        :param args: Other supportive arguments
        :param kwargs: Other supportive arguments
        :return: pd.DataFrame of all simulated results.
        """
        key, params = self._parse_params(params)
        if dsample:
            dsamples = []
        table = pd.DataFrame(columns=true_ps, index=params)
        for true_p in true_ps:
            column = self.powers(true_p, {key: params}, *args, **kwargs)
            if dsample:
                column, _dsample = column
                dsamples.append(_dsample)
            table[true_p] = column
        ret = table
        if dsample:
            dsamples = pd.concat(dsamples, keys=true_ps,
                                 axis=0).reset_index(level=1)
            ret = [ret, dsamples]
        return ret


def qqplot(true_p, cdfs: pd.Series):
    assert true_p in BRAVO.quantiles.index
    quantiles = BRAVO.quantiles.loc[true_p][:-1]
    plt.plot(quantiles)
    plt.plot(cdfs)
    plt.ylim([min(quantiles), max(quantiles)])
    plt.legend()
    plt.xlabel("quantile")
    plt.ylabel("samples")


def save_fig(fname, fig: plt.Figure = None, fpath=join("..", "figures")):
    if not exists(fpath):
        makedirs(fpath)
    to = join(fpath, fname)
    if fig is not None:
        fig.savefig(to)
        return
    plt.savefig(to)


def bravo_check(n=100000, m=5000):
    # Check if the bravo test is accurate. Replicate the result form
    # the bravo paper for amount of counting
    # Lindeman et al. 2012 Table 1
    true_ps = [0.7, 0.65, 0.6, 0.58, 0.55, 0.54, 0.53, 0.52, 0.51, 0.505]
    n_plot = len(true_ps)
    n_col = 3
    n_row = ceil(n_plot/n_col)

    figure = plt.figure(figsize=[20, 20])
    bravo_simulation = AuditSimulation(BRAVO, n, m)
    for i, true_p in enumerate(true_ps):
        print(i, true_p)
        plt.subplot(n_row, n_col, i+1)
        power, dist = \
            bravo_simulation.power(true_p, dsample=True, p=true_p, alpha=0.1)
        percentile = 0
        cumulative = {}
        for index in sorted(dist.index):
            percentile += dist[index]
            cumulative[index] = percentile
        cumulative = {value: key for key, value in cumulative.items()}
        cumulative = pd.Series(cumulative)
        qqplot(true_p, cumulative)
    save_fig("bravo_check.png", figure)
    plt.show()


def bayesian_check(n=10000):
    # Sanity check for bayesian auditing
    # Rivest & Shen 2012. Table 4
    margins = [0, 0.005, 0.01, 0.015, 0.02, 0.025,
               0.03, 0.035, 0.04, 0.045, 0.05]
    true_ps = [0.5+i/2 for i in margins]

    bayesian_simulation = AuditSimulation(Bayesian, n, m=500)
    mean_numbers = {}
    for true_p in true_ps[:1]:
        print(true_p)
        power, dist = bayesian_simulation.power(true_p, progression=True,
                                                dsample=True)
        print(dist)
        mean_number = sum([i * j for i, j in dist.items()])
        mean_numbers[true_p] = mean_number
    mean_numbers = pd.Series(mean_numbers)
    print(mean_numbers)
    return mean_numbers


def clip_check():
    n = 50000
    true_p = 0.6
    alpha = 0.1
    clip_simulation = AuditSimulation(Clip, n, m=1000)

    power, dist = clip_simulation.power(true_p, True, dsample=True,
                                        n=n, alpha=0.1, conservative=False)
    print(sum([i * j for i, j in dist.items()]))
    return dist


def type1_power_plot(*args):
    # Key should be the plot name
    types = ["name", "type1", "power"]
    if not args:
        return
    for i, val in enumerate(args):
        i = i % len(types)
        # The name of plot
        if i == 0:
            line_name = val
        elif i == 1:
            # Get the type1 error column
            type1 = val
        else:
            # Get the power
            power = val
            # Plot with legend
            plt.plot(type1, power, label=line_name)
    plt.legend()
    plt.xlabel("type1")
    plt.ylabel("power")
    assert i == 2
    # Get back current figure
    return plt.gcf()


def parse_table(table: pd.DataFrame, audit_type):
    args = []
    type1 = table[0.5]
    for p in table.columns:
        # Skip the type1
        if p == 0.5:
            continue
        args += [f"{audit_type}_{p}", type1, table[p]]
    return args


if __name__ == "__main__":
    # Sanity check for bravo auditing
    # bravo_check(n=10000, m=500)

    # Sanity check for bayesian auditing
    # bayesian_check(n=10000)

    # Sanity Check for Clip auditing
    # clip_check()

    # Code for making the comparison plot
    # n = 100000
    # m = 2000
    n = 10000
    m = 1000

    # For BRAVO auditing
    # true_ps = [0.7, 0.65, 0.6, 0.58, 0.55, 0.54, 0.53, 0.52, 0.51, 0.505]
    # bravo_params = {"alpha": list(np.linspace(0.005, 0.15, 15))}
    # bravo = AuditSimulation(BRAVO, n, m)
    #
    # args = []
    # for true_p in true_ps:
    #     print(true_p)
    #     power = bravo.powers(true_p, bravo_params, p=true_p)
    #     type1 = bravo.powers(0.5, bravo_params, p=true_p)
    #     args.append(f"bravo_{true_p}")
    #     args.append(type1)
    #     args.append(power)

    # Plot for Bayesian auditing
    # true_ps = [0.5, 0.7, 0.65, 0.6, 0.58, 0.55,
    #            0.54, 0.53, 0.52, 0.51, 0.505]
    true_ps = [0.5, 0.7, 0.6, 0.58, 0.55, 0.52, 0.505]
    bayesian_params = {"thresh": list(np.linspace(0.85, 0.95, 5)) +
                       list(np.linspace(0.95, 0.999, 10))}
    bayesian_audit = AuditSimulation(Bayesian, n, m)
    bayesian_table = bayesian_audit.tabular_power(true_ps, bayesian_params)
    args = parse_table(bayesian_table, "bayesian")
    fig = type1_power_plot(*args)
    fig.show()

    # fig = type1_power_plot(*args)
    # fig.show()
