import logging
console_logger = logging.getLogger("console_logger")
console_logger.setLevel(logging.ERROR)
import pytest

import pandas as pd
from auditing_setup.audit_methods import BRAVO, Bayesian, Clip
from auditing_setup.raw_distributions import AuditMethodDistributionComputer
from auditing_setup.expected_statistics import ExpectedStatisticsComputer


def test_bravo():
    # Check if the bravo test is accurate. Replicate the result form
    # the bravo paper for amount of counting
    # Lindeman et al. 2012 Table 1
    alpha = 0.1
    n = 100000

    quantiles = pd.DataFrame(
        [
            [12, 22, 38, 60, 131, 30],
            [23, 38, 66, 108, 236, 53],
            [49, 84, 149, 244, 538, 119],
            [77, 131, 231, 381, 840, 184],
            [93, 332, 587, 974, 2157, 469],
            [301, 518, 916, 1520, 3366, 730],
            [531, 914, 1619, 2700, 5980, 1294],
            [1188, 2051, 3637, 6053, 13455, 2900],
            [4725, 8157, 14486, 24149, 53640, 11556],
            [18839, 32547, 57838, 96411, 214491, 46126]
        ],
        index=[0.7, 0.65, 0.60, 0.58, 0.55, 0.54, 0.53, 0.52, 0.51, 0.505],
        columns=[0.25, 0.5, 0.75, 0.9, 0.99, "mean"]
    )
    quantiles = quantiles.drop(["mean"], axis=1)
    for true_p in quantiles.index:
        m = max(quantiles.loc[true_p])
        if m > 1000:
            continue
        esc = ExpectedStatisticsComputer(BRAVO, n, m)
        stats = esc.compute_statistics(true_p, p=true_p, alpha=alpha)
        for column in quantiles.columns:
            entry = f"unconditional_quantile{column:.2f}"
            assert abs(quantiles.loc[true_p, column] - stats[entry]) < 5, \
                f"{quantiles.loc[true_p, column]} {stats[entry]}"


def bayesian_check(n=10000):
    # Sanity check for bayesian auditing
    # Rivest & Shen 2012. Table 4
    margins = [0, 0.005, 0.01, 0.015, 0.02, 0.025,
               0.03, 0.035, 0.04, 0.045, 0.05]
    true_ps = [0.5+i/2 for i in margins]

    bayesian_simulation = AuditMethodDistributionComputer(Bayesian, n, m=500)
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
    clip_simulation = AuditMethodDistributionComputer(Clip, n, m=1000)

    power, dist = clip_simulation.power(true_p, True, dsample=True,
                                        n=n, alpha=alpha, conservative=False)
    print(sum([i * j for i, j in dist.items()]))
    return dist

