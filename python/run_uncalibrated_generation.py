import argparse
from os import path

from auditing_setup.expected_statistics import audit_method_expected_statistics
import csv
# The following import is needed because `eval` is used for audit methods
from auditing_setup.audit_methods import *

from parse_election import parse_election_config, make_path


def main_run_uncalibrated_generation():
    parser = argparse.ArgumentParser()
    parser.add_argument("election_config")
    parser.add_argument("method_config")

    args = parser.parse_args()
    election_config = args.election_config
    method_config = args.method_config

    assert method_config.endswith(".csv")
    assert election_config.endswith(".csv")
    run_uncalibrated_generation(election_config, method_config)


def run_uncalibrated_generation(election_config, method_config):
    global_kwargs, true_ps, save = parse_election_config(election_config)
    for key in ("p_0", "tol", "max_iter", "risk_lim", "fpath"):
        if key in global_kwargs:
            global_kwargs.pop(key)

    with open(method_config) as config_file:
        config_reader = csv.reader(config_file)
        config_list = list(config_reader)
        for audit_setting in config_list:
            audit_method = eval(audit_setting[0])
            # First entry to be parsed by these few lines
            audit_kwargs = dict()
            for key in audit_kwargs:
                if key != "param_name":
                    audit_kwargs[key] = eval(audit_kwargs[key])

            # The rest of the lines are variable length, automatically parse them (additional parameters)
            for ind in range(1, len(audit_setting), 2):
                audit_kwargs[audit_setting[ind]] = eval(audit_setting[ind + 1])
            print(audit_kwargs)

            base_path = "uncalibrated_data"
            fpath = make_path(
                base_path,
                global_kwargs["n"],
                global_kwargs["m"],
                global_kwargs["replacement"],
                global_kwargs["step"]
            )
            fpath = path.join(fpath, audit_method.name)
            audit_method_expected_statistics(audit_method, [audit_kwargs], true_ps=true_ps, save=True,
                                             fpath=fpath, include_risk=True, **global_kwargs)


if __name__ == "__main__":
    """
    The entry for the calibration for a method are:
    Method Name, Parameter Name, min_parameter, max_parameter, *(parameter names, values)
    """
    import logging
    logger = logging.getLogger("console_logger")
    logger.setLevel(logging.ERROR)
    main_run_uncalibrated_generation()
