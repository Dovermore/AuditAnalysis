import os
from os import path
import matplotlib.pyplot as plt
import pandas as pd
from collections import defaultdict


def generate_plot(all_data_path):
    # Get risk lim
    for method_data_path in os.listdir(all_data_path):
        _, risk_lim = method_data_path.split("_")
        break

    all_data = defaultdict(pd.DataFrame)
    for method_data_path in os.listdir(all_data_path):
        method, _ = method_data_path.rsplit("_", 1)
        for data_file_name in os.listdir(path.join(all_data_path, method_data_path)):
            data_name = path.splitext(data_file_name)[0]
            data_type = data_name.replace(f"{method}_", "")
            data_file_full_path = path.join(all_data_path, method_data_path, data_file_name)
            data = pd.read_csv(data_file_full_path, header=0)
            all_data[data_type] = pd.concat([all_data[data_type], data])

    for data_type in all_data:
        print(data_type)
        all_data[data_type] = all_data[data_type].set_index("legend")
        data = all_data[data_type]
        plt.figure(figsize=[10, 10])
        for method, method_data in data.iterrows():
            print("=======")
            print(method_data)
            print(method_data.index)
            plt.plot(method_data)
        plt.xticks(data.columns)
        plt.legend(data.index)
        plt.title(data_type)
        plt.show()


# scratch tests
if __name__ == "__main__":
    n = 20000
    m = 1000
    all_data_path = path.join("calibrated_data", f"election_n={n:06d}_m={m:05d}")
    generate_plot(all_data_path)
