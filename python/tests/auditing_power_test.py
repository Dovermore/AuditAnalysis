from math import ceil

import pandas as pd
from matplotlib import pyplot as plt

from audit_method import BRAVO, Bayesian, Clip
from audit_power import AuditSimulation
from binomial_plotting import save_fig


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
        not_qqplot(true_p, cumulative)
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
                                        n=n, alpha=alpha, conservative=False)
    print(sum([i * j for i, j in dist.items()]))
    return dist


if __name__ == "__main__":
    # Sanity check for bravo auditing
    bravo_check(n=10000, m=500)

    # Sanity check for bayesian auditing
    bayesian_check(n=10000)

    # Sanity Check for Clip auditing
    clip_check()


def not_qqplot(true_p, cdfs: pd.Series):
    assert true_p in BRAVO.quantiles.index
    quantiles = BRAVO.quantiles.loc[true_p][:-1]
    plt.plot(quantiles)
    plt.plot(cdfs)
    plt.ylim([min(quantiles), max(quantiles)])
    plt.legend()
    plt.xlabel("quantile")
    plt.ylabel("samples")