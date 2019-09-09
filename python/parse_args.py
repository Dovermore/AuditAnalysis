import csv
from os import path


def parse_election_config(election_config):
    with open(election_config) as config_file:
        config_reader = csv.reader(config_file)
        n_lines = int(next(config_reader)[0])
        print("n_lines:", n_lines)

        election_kwargs_list = []
        # Read Null Election Setup
        for i in range(n_lines):
            election_keys = ["n", "m", "p", "step", "replacement", "multiprocessing"]
            election_kwargs = {key: eval(value) for key, value in zip(election_keys, next(config_reader))}
            election_kwargs_list.append(election_kwargs)

        # Read Calibration Parameters
        calibration_keys = ["risk_lim", "tol", "max_iter"]
        calibration_kwargs = {key: eval(value) for key, value in zip(calibration_keys, next(config_reader))}

        # Read Alternative Election Probabilities
        alternative_ps = [eval(p) for p in next(config_reader)]

        return election_kwargs_list, calibration_kwargs, alternative_ps

def parse_audit_method_config(method_config):
    audit_kwargs_list = []
    with open(method_config) as config_file:
        config_reader = csv.reader(config_file)
        audit_parameters = ["audit_method", "param_name", "param_min", "param_max"]
        config_list = list(config_reader)
        for audit_setting in config_list:

            # First 4 entries to be parsed by these few lines
            audit_kwargs = dict(zip(audit_parameters, audit_setting[:4]))
            for key in audit_kwargs:
                if key != "param_name":
                    audit_kwargs[key] = eval(audit_kwargs[key])

            # The rest of the lines are variable length, automatically parse them (additional parameters)
            for ind in range(4, len(audit_setting), 2):
                audit_kwargs[audit_setting[ind]] = eval(audit_setting[ind + 1])

            audit_kwargs_list.append(audit_kwargs)
    return audit_kwargs_list


def make_path(base, n, m, replacement, step):
    return path.join(base, f"election_n={n:06d}_m={m:05d}_replacement={replacement}_step={step}")
