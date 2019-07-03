import pandas as pd
from auditing_setup.audit_sample_number_analysis import SampleStatisticsSimulation
from auditing_setup.audit_method import Bayesian, HyperGeomBRAVO, KMart
from auditing_setup.audit_power import to_csv
import numpy as np
from os.path import join
from collections import defaultdict as dd


def make_legend(audit_method, **kwargs):
    legend = f"{audit_method.name:8}"
    for key, value in kwargs.items():
        legend += f" | {key}:{value}"
    print(legend)
    return legend


def power_data_generation(audit_method, audit_params, n, m, true_ps=np.linspace(0.45, 0.75, 25), save=True):
    fpath = join("..", "new_data", f"{n:06}{m:04}_wo")
    sss = SampleStatisticsSimulation(audit_method, n, m, False)

    statistics_dfs = dd(lambda: pd.DataFrame())
    for params in audit_params:
        legend = make_legend(audit_method, **params)
        statistics_data = dd(lambda: {"legend": legend})
        for true_p in true_ps:
            statistics = sss.compute_statistics(true_p, **params)
            for stat_type in statistics.index:
                statistics_data[stat_type][true_p] = statistics[stat_type]

        for stat_type in statistics_data:
            statistics_dfs[stat_type] = statistics_dfs[stat_type]\
                .append(statistics_data[stat_type], ignore_index=True)
    if save:
        for stat_type in statistics_dfs:
            to_csv(statistics_dfs[stat_type], f"{audit_method.name}_{stat_type}.csv", fpath)
    return statistics_dfs


if __name__ == "__main__":
    n = 501
    # true_ps = list(np.linspace(0.4, 1, 40))
    # m = -1
    # bravo_params = [
    #     {"alpha": 0.07, "p": 0.7},
    #     {"alpha": 0.18, "p": 0.55},
    # ]
    #
    # bayesian_params = [
    #     {"a": 1, "b": 1, "thresh": 0.99776},
    #     {"a": 4, "b": 1, "thresh": 0.999075},
    #     {"a": 1, "b": 4, "thresh": 0.99555},
    # ]

    m = -1
    bravo_params = [
        {"alpha": 0.072, "p": 0.7},
        {"alpha": 0.25, "p": 0.55},
    ]

    hyper_geom_bravo_params = [
        {"alpha": 0.063, "p": 0.7},
        {"alpha": 0.195, "p": 0.55},
    ]

    bayesian_params = [
        {"a": 1, "b": 1, "thresh": 0.9939},
        {"a": 4, "b": 1, "thresh": 0.99835},
        {"a": 1, "b": 4, "thresh": 0.97251},
    ]

    kmart_params = [
        {"alpha": 0.065},
    ]

    bayesian_params = [
        {"a": 1, "b": 1, "thresh": 0.95},
    ]

    # power_data_generation(BRAVO, bravo_params, n, m)
    # power_data_generation(HyperGeomBRAVO, hyper_geom_bravo_params, n, m)
    power_data_generation(Bayesian, bayesian_params, n, m)
    # power_data_generation(KMart, kmart_params, n, m)
