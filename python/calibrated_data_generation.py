import pandas as pd
from auditing_setup.audit_sample_number_analysis import SampleStatisticsSimulation
from auditing_setup.audit_method import Bayesian, HyperGeomBRAVO, KMart
from auditing_setup.audit_power import to_csv
import numpy as np
from os.path import join


def make_legend(audit_method, **kwargs):
    legend = f"{audit_method.name:8}"
    for key, value in kwargs.items():
        legend += f" | {key}:{value}"
    print(legend)
    return legend


def power_data_generation(audit_method, audit_params, n, m,
                          true_ps=np.linspace(0.5, 0.75, 20)):
    fpath = join("..", "data_calibrated",
                 f"{n:06}{m:04}_wo")
    legends = []
    sss = SampleStatisticsSimulation(audit_method, n, m, False)

    power_df = pd.DataFrame()
    power_mean_df = pd.DataFrame()
    power_mean_with_handcount_df = pd.DataFrame()
    power_9th_df = pd.DataFrame()
    power_median_df = pd.DataFrame()

    for params in audit_params:
        legend = make_legend(audit_method, **params)

        power_data = {"legend": legend}
        power_mean_data = {"legend": legend}
        power_mean_with_handcount_data = {"legend": legend}
        power_9th_data = {"legend": legend}
        power_median_data = {"legend": legend}

        legends.append(legend)
        for true_p in true_ps:
            statistics = sss.compute_statistics(true_p, **params)

            power = statistics["power"]
            power_data[true_p] = power

            power_mean = statistics["powermean"]
            power_mean_data[true_p] = power_mean

            power_mean_with_handcount_data[true_p] = power_mean + (1 - power) * n

            power_9th = statistics["power>=0.90"]
            power_9th_data[true_p] = power_9th

            power_median = statistics["power>=0.50"]
            power_median_data[true_p] = power_median

        power_df = power_df.append(power_data, ignore_index=True)
        power_mean_df = power_mean_df.append(power_mean_data, ignore_index=True)
        power_mean_with_handcount_df = \
            power_mean_with_handcount_df.append(power_mean_with_handcount_data,
                                                ignore_index=True)
        power_9th_df = power_9th_df.append(power_9th_data, ignore_index=True)
        power_median_df = power_median_df.append(power_median_data, ignore_index=True)

    to_csv(power_df, f"{audit_method.name}_power", fpath)
    to_csv(power_mean_df, f"{audit_method.name}_power_mean_size", fpath)
    to_csv(power_mean_with_handcount_df, f"{audit_method.name}_power_mean_size", fpath)
    to_csv(power_9th_df, f"{audit_method.name}_power_090quantile_size", fpath)
    to_csv(power_median_df, f"{audit_method.name}_power_median_size", fpath)

    return power_df, power_mean_df, power_mean_with_handcount_df, power_9th_df, power_median_df


if __name__ == "__main__":
    n = 500
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

    m = 100
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

    # power_data_generation(BRAVO, bravo_params, n, m)
    power_data_generation(HyperGeomBRAVO, hyper_geom_bravo_params, n, m)
    power_data_generation(Bayesian, bayesian_params, n, m)
    power_data_generation(KMart, kmart_params, n, m)
