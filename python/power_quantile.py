"""
This is the actual file simulating quantile for power for different audit
setting.
"""
from audit_power import to_csv

import numpy as np
from os.path import join
from audit_sample_number_analysis import SampleStatisticsSimulation
from multiprocessing import Process
from audit_method import Bayesian, BRAVO, Clip


n = 10000
power = 0.9
replacement = False

# TODO Read calibrated thresholds and put in computation


fpath = join("..", "data/statistics",
             f"{n:06}{power*100:02.0f}_{'w' if replacement else 'wo'}")


def bayesian_statistics(n=n, power=power):
    true_ps = [0.7, 0.58, 0.52]
    bayesian_params = {"thresh":
                           list(np.linspace(0.9, 0.95, 3)) +
                           list(np.linspace(0.955, 0.9999, 20))}
    bayesian_auditors = {"partisan_w1": {"a": 9, "b": 1},
                         "nonpartisan": {"a": 1, "b": 1},
                         "partisan_l1": {"a": 1, "b": 9},
                         "partisan_w2": {"a": 4, "b": 1},
                         "partisan_l2": {"a": 1, "b": 4}}

    def single_bayesian_statistics(true_p, a, b):
        sss = SampleStatisticsSimulation(Bayesian, n, power, replacement)
        all_statistics = \
            sss.compute_param_dict_statistics(true_p, bayesian_params,
                                              a=a, b=b)
        to_csv(all_statistics,
               f"bayesian_statistics{true_p*100:02.0f}{a:02}{b:02}.csv",
               fpath=fpath)

    for partisan in bayesian_auditors:
        for true_p in true_ps:
            a = bayesian_auditors[partisan]["a"]
            b = bayesian_auditors[partisan]["b"]
            sub_process = Process(target=single_bayesian_statistics,
                                  args=(true_p, a, b))
            sub_process.start()


min_alpha = 0.005
max_alpha = 0.3
n_param = 20


def bravo_statistics(n=n, power=power):
    # BRAVO auditing
    # Reset True P
    true_ps = [0.7, 0.58, 0.52]
    bravo_params = {"alpha": list(np.linspace(min_alpha,
                                              max_alpha, n_param))}

    def single_bravo_statistics(true_p, reported):
        sss = SampleStatisticsSimulation(BRAVO, n, power, replacement)
        all_statistics = \
            sss.compute_param_dict_statistics(true_p, bravo_params, p=reported)
        to_csv(all_statistics,
               f"bravo_statistics{reported*100:02.0f}{true_p*100:02.0f}.csv",
               fpath=fpath)

    for true_p in true_ps:
        for reported in true_ps:
            sub_process = Process(target=single_bravo_statistics,
                                  args=(true_p, reported))
            sub_process.start()


if __name__ == "__main__":
    # bayesian_statistics()
    bravo_statistics()
