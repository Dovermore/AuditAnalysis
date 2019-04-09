from audit_method import Bayesian, BRAVO, Clip
from stochastic_simulation import stochastic_process_simulation
from collections import defaultdict as dd

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
            column = self.powers(true_p, params, *args, **kwargs)
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


if __name__ == "__main__":
    # BRAVO test
    true_ps = [0.7, 0.65, 0.6, 0.58, 0.55, 0.54, 0.53, 0.52, 0.51, 0.505]
    n = 1000
    m = 100

    bravo_simulation = AuditSimulation(BRAVO, n, m)
    for true_p in true_ps:
        power, dist = \
            bravo_simulation.power(true_p, dsample=True, p=true_p, alpha=0.1)
        print(dist)

    # 0.5 for simulating risk-limit
    # ps = [0.5, 0.52, 0.55, 0.6, 0.7]
    #
    # bayesian_params = {"threshold": [0.8, 0.85] +
    #                    list(np.linspace(0.9, 1, 13))}
    # bravo_params = {"alpha": list(np.linspace(0.005, 0.3, 15))}

    # plt.figure(figsize=[20, 10])
    # plt.subplot(1, 2, 1)
    #
    # for p in ps:
    #     plt.plot(bravo_power[p].values(), bravo_type1.values())
    # plt.xlabel("power")
    # plt.ylabel("type1")
    #
    # plt.subplot(1, 2, 2)
    # for p in ps:
    #     plt.plot(bravo_power[p].keys(), bravo_power[p].values(), label=str(p))
    # plt.xlabel("threshold")
    # plt.ylabel("power")
    # plt.legend()

