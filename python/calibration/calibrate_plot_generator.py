import os
from os import path
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict


def generate_statistics_plot(all_data_path, base_fig_path="figures", base_table_path="tables"):
    # Get risk lim
    has_risk = True
    try:
        for method_data_path in os.listdir(all_data_path):
            _, risk_lim = method_data_path.rsplit("_", 1)
    except:
        has_risk = False

    all_data = defaultdict(pd.DataFrame)
    for method_data_path in os.listdir(all_data_path):
        if has_risk:
            method, _ = method_data_path.rsplit("_", 1)
        else:
            method = method_data_path

        for data_file_name in os.listdir(path.join(all_data_path, method_data_path)):
            data_name = path.splitext(data_file_name)[0]
            print(method, data_name, data_file_name)
            data_type = data_name.replace("{}_".format(method), "")
            data_file_full_path = path.join(all_data_path, method_data_path, data_file_name)
            data = pd.read_csv(data_file_full_path, header=0)
            all_data[data_type] = pd.concat([all_data[data_type], data])

    for data_type in all_data:
        if data_type in ["pdf", "cdf"]:
            continue
        print(data_type)
        all_data[data_type] = all_data[data_type].set_index("legend")
        data = all_data[data_type]
        plt.figure(figsize=[14, 14])
        ls_generator = line_style_generator(data.shape[0])
        for method, method_data in data.iterrows():
            print("=======")
            print(method_data)
            print(method_data.index)
            plt.plot(method_data, **next(ls_generator), alpha=0.8)
        plt.xlim([0, None])
        plt.ylim([0, None])
        plt.xticks(data.columns)
        plt.legend(data.index)
        plt.title("{}-{}".format(all_data_path.rsplit("/")[-1], data_type))
        fig_path = path.join(base_fig_path, path.basename(all_data_path))
        if not path.exists(fig_path):
            os.makedirs(fig_path)
        plt.savefig(path.join(fig_path, data_type.replace(".", "_")+".png"))
        plt.tight_layout()

        table_path = path.join(base_table_path, path.basename(all_data_path))
        if not path.exists(table_path):
            os.makedirs(table_path)
        data.to_csv(path.join(table_path, data_type.replace(".", "_")+".csv"))


def simple_lw_fn(i, n, max=8, min=4):
    return max - (max-min) * (i/n)


def line_style_generator(n, ls_list=('-','--','-.',':'), lw_fn=simple_lw_fn):
    for i in range(n):
        lw = lw_fn(i, n)
        ls = ls_list[i % len(ls_list)]
        yield {
            "linestyle": ls,
            "linewidth": lw,
        }


# scratch tests
if __name__ == "__main__":
    # base_path = path.abspath("calibrated_data")
    option = 4

    if option == 0:
        base_path = path.abspath("new_calibrate_full")
        for data_path in os.listdir(base_path):
            data_path = path.join(base_path, data_path)
            if not path.isdir(data_path):
                continue
            generate_statistics_plot(data_path, base_fig_path="new_figures")
    elif option == 1:
        base_path = path.abspath("uncalibrate_full")
        for data_path in os.listdir(base_path):
            data_path = path.join(base_path, data_path)
            if not path.isdir(data_path):
                continue
            generate_statistics_plot(data_path, base_fig_path="uncalibrated_figures", base_table_path="uncalibrated_tables")

    elif option == 2:
        base_path = path.abspath("minstop_calibrate_full")
        for data_path in os.listdir(base_path):
            data_path = path.join(base_path, data_path)
            if not path.isdir(data_path):
                continue
            generate_statistics_plot(data_path, base_fig_path="minstop_calibrate_full_figures", base_table_path="minstop_calibrate_full_tables")

    elif option == 3:
        base_path = path.abspath("new_calibrate_full/n=005000_m=00500_p=0.500_replacement=False_step=1")
        data_path = base_path
        generate_statistics_plot(data_path, base_fig_path="new_figures")

    elif option == 4:
        base_path = path.abspath("xtreme_prior_full")
        for data_path in os.listdir(base_path):
            data_path = path.join(base_path, data_path)
            if not path.isdir(data_path):
                continue
            generate_statistics_plot(data_path, base_fig_path="xtreme_prior_full_figures", base_table_path="xtreme_prior_full_tables")


