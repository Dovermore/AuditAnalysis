from calibrated_data_generation import power_data_generation
from audit_method import BRAVO, Bayesian, Clip
from matplotlib import pyplot as plt
import numpy as np
from binomial_plotting import save_fig


plot_styles = [":", "--", "-.", "-*", "-"]
plot_colours = ["m", "g", "b", "k"]


def plot_calibrated_df(dfs, title):
    legends = []
    for i, df in enumerate(dfs):
        plot_colour = plot_colours[i]
        for row, row_data in df.iterrows():
            plot_style = plot_styles[row]
            legends.append(row_data["legend"])
            data = row_data.drop("legend")
            plt.plot(data, plot_colour+plot_style)
    plt.legend(legends)
    plt.title(title)


if __name__ == "__main__":
    true_ps = np.linspace(0.45, 0.75, 40)

    n = 500
    m = -1
    bravo_params = [
        {"alpha": 0.07, "p": 0.7},
        {"alpha": 0.18, "p": 0.55},
    ]

    bayesian_params = [
        {"a": 1, "b": 1, "thresh": 0.99776},
        {"a": 4, "b": 1, "thresh": 0.999075},
        {"a": 1, "b": 4, "thresh": 0.99555},
    ]
    clip_params = [
        {"n": n, "alpha": 0.075}
    ]

    powers = []
    power_means = []
    power_9ths = []
    power_medians = []
    power, power_mean, power_9th, power_median = \
        power_data_generation(BRAVO, bravo_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    power, power_mean, power_9th, power_median = \
        power_data_generation(Bayesian, bayesian_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    power, power_mean, power_9th, power_median = \
        power_data_generation(Clip, clip_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(powers, "power")
    save_fig(f"calibrated_power_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_means, "mean size")
    save_fig(f"calibrated_power_mean_size_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_9ths, "0.9 quantile size")
    save_fig(f"calibrated_power_090quantile_size_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_medians, "median size")
    save_fig(f"calibrated_power_median_size_{n:06}_{m:04}.png")
    plt.show()

    n = 500
    m = 100
    bravo_params = [
        {"alpha": 0.072, "p": 0.7},
        {"alpha": 0.25, "p": 0.55},
    ]
    bayesian_params = [
        {"a": 1, "b": 1, "thresh": 0.9939},
        {"a": 4, "b": 1, "thresh": 0.99835},
        {"a": 1, "b": 4, "thresh": 0.97251},
    ]
    clip_params = [
        {"n": n, "alpha": 0.0815}
    ]

    powers = []
    power_means = []
    power_9ths = []
    power_medians = []
    power, power_mean, power_9th, power_median = \
        power_data_generation(BRAVO, bravo_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    power, power_mean, power_9th, power_median = \
        power_data_generation(Bayesian, bayesian_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    power, power_mean, power_9th, power_median = \
        power_data_generation(Clip, clip_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(powers, "power")
    save_fig(f"calibrated_power_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_means, "mean size")
    save_fig(f"calibrated_power_mean_size_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_9ths, "0.9 quantile size")
    save_fig(f"calibrated_power_090quantile_size_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_medians, "median size")
    save_fig(f"calibrated_power_median_size_{n:06}_{m:04}.png")
    plt.show()

    n = 10000
    m = 500
    bravo_params = [
        {"alpha": 0.085, "p": 0.55},
        {"alpha": 0.0591, "p": 0.7},
    ]
    bayesian_params = [
        {"a": 1, "b": 1, "thresh": 0.996322},
        {"a": 4, "b": 1, "thresh": 0.99902},
        {"a": 1, "b": 4, "thresh": 0.9892},
    ]
    clip_params = [
        {"n": n, "alpha": 0.0815}
    ]

    powers = []
    power_means = []
    power_9ths = []
    power_medians = []

    power, power_mean, power_9th, power_median = \
        power_data_generation(BRAVO, bravo_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    power, power_mean, power_9th, power_median = \
        power_data_generation(Bayesian, bayesian_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    power, power_mean, power_9th, power_median = \
        power_data_generation(Clip, clip_params, n, m, true_ps)
    powers.append(power)
    power_means.append(power_mean)
    power_9ths.append(power_9th)
    power_medians.append(power_median)

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(powers, "power")
    save_fig(f"calibrated_power_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_means, "mean size")
    save_fig(f"calibrated_power_mean_size_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_9ths, "0.9 quantile size")
    save_fig(f"calibrated_power_090quantile_size_{n:06}_{m:04}.png")
    plt.show()

    plt.figure(figsize=[7, 7])
    plot_calibrated_df(power_medians, "median size")
    save_fig(f"calibrated_power_median_size_{n:06}_{m:04}.png")
    plt.show()
