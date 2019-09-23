from auditing_setup.election_setting import Election
from auditing_setup.audit_process import audit_process_simulation
from collections import defaultdict as dd
from os import makedirs
from os.path import exists, join

import pandas as pd
import matplotlib.pyplot as plt


class AuditMethodDistributionComputer:
    def __init__(self, audit_method):
        self.audit_method = audit_method

    def power(self, election: Election, dsample=False, cdf=False, audit_process_kw={}, *args, **kwargs):
        """
        Mostly used as helper for computing a single power
        :param election: The election setup to run power on and to support audit_class
        :param dsample: distribution of sample votes
        :param cdf: should output be cdf instead of pdf
        :param audit_process_kw: Other keyword arguments to feed to audit process
        :param args: Parameters supporting the creation of auditing function
        :param kwargs: Parameters supporting the creation of auditing function
        :return: The power of current simulation
        """
        audit_f = self.audit_method(election=election, *args, **kwargs)
        reject_dict = audit_process_simulation(audit_f, election, **audit_process_kw)
        power = sum(reject_dict.values())
        ret = power
        if dsample:
            dsample = dd(float)
            # (t, y_t)
            for key in reject_dict:
                t, y_t = key
                if t > election.m:
                    continue
                proba = reject_dict[key]
                dsample[t] += proba
            
            ret = [power, pd.Series(dsample).sort_values(axis="index")]
        if cdf and dsample:
            ret[1] = self.dsample_to_cdf(ret[1], election.m)
        return ret

    @staticmethod
    def dsample_to_cdf(dsample, m):
        total_proba = 0
        new_dsample = dd(float)
        i = 0
        for t in sorted(dsample.index):
            if t > m:
                continue
            while i < t:
                new_dsample[i] = total_proba
                i += 1
            total_proba += dsample[t]
        while i <= m:
            new_dsample[i] = total_proba
            i += 1
        return pd.Series(new_dsample).sort_values(axis="index")

    @staticmethod
    def _parse_params(params):
        key = None
        for key in params:
            break
        return key, params[key]


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
    assert len(args) and i == 2
    # Get back current figure
    return plt.gcf()


def parse_table(table: pd.DataFrame, audit_type):
    args = []
    type1 = table[0.5]
    for p in table.columns:
        # Skip the type1
        if p == 0.5:
            continue
        args += ["{}_{}".format(audit_type, p), type1, table[p]]
    return args


def split_args(args):
    individual_args = [(args[3*i], args[3*i+1], args[3*i+2])
                       for i in range(len(args)//3)]
    true_ps_bucket = dd(list)
    for individual_arg in individual_args:
        # Split and get the true probability
        p = individual_arg[0].split("_")[-1]
        true_ps_bucket[p].append(individual_arg)
    return true_ps_bucket


def compute_expected_number(dsample: dict, m):
    proportion = 1 - sum(dsample.values())
    return proportion * m + sum((i * j for i, j in dsample.items()))


def to_csv(data: (pd.DataFrame, pd.Series), fname, fpath=join("..", "data"), dsample=False):
    """
    Save distribution data frame to csv file, based on given file type
    """
    if not exists(fpath):
        makedirs(fpath)
    full_name = fname
    full_path = join(fpath, full_name)
    # This part names the file with _i in the end
    # extension = ""
    # if "." in full_name:
    #     fname, extension = list(fname.rsplit(".", 1))
    # i = 1
    # while exists(full_path):
    #     full_name = fname + f"_{i}." + extension
    #     full_path = join(fpath, full_name)
    #     i += 1
    print("Saving to:", full_path)
    if dsample:
        data.to_csv(path_or_buf=full_path,
                    index_label=["true_p", "sample_number"])
    else:
        data.to_csv(path_or_buf=full_path)

