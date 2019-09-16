import os
from os import path
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict


def generate_plot(all_data_path, base_fig_path="figures"):
    # Get risk lim
    for method_data_path in os.listdir(all_data_path):
        _, risk_lim = method_data_path.split("_")
        break

    all_data = defaultdict(pd.DataFrame)
    for method_data_path in os.listdir(all_data_path):
        method, _ = method_data_path.rsplit("_", 1)
        for data_file_name in os.listdir(path.join(all_data_path, method_data_path)):
            data_name = path.splitext(data_file_name)[0]
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
        for method, method_data in data.iterrows():
            print("=======")
            print(method_data)
            print(method_data.index)
            plt.plot(method_data)
        plt.xticks(data.columns)
        plt.legend(data.index)
        plt.title(data_type)
        fig_path = path.join(base_fig_path, path.basename(all_data_path))
        if not path.exists(fig_path):
            os.makedirs(fig_path)
        plt.savefig(path.join(fig_path, data_type.replace(".", "_")+".png"))
        plt.show()


# scratch tests
if __name__ == "__main__":
    # base_path = path.abspath("calibrated_data")
    base_path = path.abspath("new_calibrate_full")
    for data_path in os.listdir(base_path):
        data_path = path.join(base_path, data_path)
        if not path.isdir(data_path):
            continue
        generate_plot(data_path, base_fig_path="new_figures")

