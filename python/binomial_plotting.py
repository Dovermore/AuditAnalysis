import sys
from os import path
import os
import re
from audit_method import Bayesian, BRAVO, Clip
import pandas as pd
from math import sqrt, ceil
import matplotlib.pyplot as plt
from collections import defaultdict as dd

type1_lim = [-0.05, 0.15]


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
            power: pd.Series = val
            if power.name == 0.5:
                continue
            # Plot with legend
            plt.plot(type1, power, label=line_name)
    plt.legend()
    plt.xlabel("type1")
    plt.ylabel("power")
    assert i == 2
    # Get back current figure
    return plt.gcf()


def save_fig(fname, fig: plt.Figure = None, fpath=path.join("..", "figures")):
    if not path.exists(fpath):
        os.makedirs(fpath)
    to = path.join(fpath, fname)
    if fig is not None:
        fig.savefig(to)
        return
    plt.savefig(to)


if __name__ == "__main__":
    p0 = str(0.5)
    data_path = path.join("..", "data")
    n = 500
    m = -1

    table_pattern = re.compile(f"^([a-z]*)_(table|power|type1)"
                               f"{n:06}{m:04}(\d*)\.csv$")
    dsample_pattern = re.compile(f"^([a-z]+)_(dsample){n:06}{m:04}(\d*)\.csv$")

    tables = {Bayesian.name: {}, BRAVO.name: dd(dict), Clip.name: {}}
    dsamples = {Bayesian.name: {}, BRAVO.name: {}, Clip.name: {}}

    for file in os.listdir(data_path):
        # Get file name
        full_file: str = path.join(data_path, file)

        # If matched table pattern
        table_match = table_pattern.match(file)
        if table_match is not None:
            print(file)
            audit_type = table_match.group(1)
            table_type = table_match.group(2)
            parameter_group = table_match.group(3)

            # If is bayesian audit simulation
            if audit_type == Bayesian.name:
                # Load Parameters
                a = int(parameter_group[:2])
                b = int(parameter_group[2:])
                tables[audit_type][(a, b)] = pd.read_csv(full_file,
                                                         index_col=0)

            elif audit_type == BRAVO.name:
                tables[audit_type][float(parameter_group)/100][table_type] = \
                    pd.read_csv(full_file, index_col=0)
            elif audit_type == Clip.name:
                tables[audit_type] = pd.read_csv(full_file, index_col=0)
            else:
                print(f"unknown audit type: {audit_type}", file=sys.stderr)

        dsamples_match = dsample_pattern.match(file)
        if dsamples_match is not None:
            # TODO add this logic
            pass

    # Get all the p used
    true_ps = list(tables[Clip.name].columns)
    if p0 in true_ps:
        true_ps.remove(p0)

    ncol = ceil(sqrt(len(true_ps)))
    nrow = ceil(len(true_ps)/ncol)

    figure: plt.Figure = plt.figure(figsize=[20.48, 20.48])
    for i, true_p in enumerate(true_ps):
        plt.subplot(nrow, ncol, i + 1)

        args = []

        # Bayesian
        bayesian_tables = tables[Bayesian.name]
        for a, b in bayesian_tables:
            # Get the DataFrame
            df = bayesian_tables[(a, b)]
            # Add name
            legend = f"{Bayesian.name}_{a:02}{b:02}"
            args.append(legend)
            # Get used Column
            type1 = df[str(p0)]
            args.append(type1)
            power = df[true_p]
            args.append(power)

        # Bravo
        bravo_tables = tables[BRAVO.name]
        for reported_p in bravo_tables:
            df_type1 = bravo_tables[reported_p]["type1"]
            df_power = bravo_tables[reported_p]["power"]

            legend = f"{BRAVO.name}_{reported_p:04.2f}"
            args.append(legend)
            type1 = df_type1[true_p]
            args.append(type1)
            power = df_power[true_p]
            args.append(power)

        # Clip
        clip_table = tables[Clip.name]
        legend = f"{Clip.name}"
        args.append(legend)
        args.append(clip_table[str(p0)])
        args.append(clip_table[true_p])

        type1_power_plot(*args)
        plt.xlim(type1_lim)
        plt.title(true_p)
    save_fig(f"overall_plot_{n}_{m}_{type1_lim[1]}full.png")

    plt.show()

