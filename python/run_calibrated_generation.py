import argparse
import csv

import contextlib

# The following import is needed because `eval` is used for audit methods
from auditing_setup.audit_methods import *
from calibration.calibration_data_generator import AuditMethodCalibrator

from parse_args import parse_election_config

from joblib import Parallel, delayed
# from joblib import Memory


def main_run_calibration():
    parser = argparse.ArgumentParser()
    parser.add_argument("election_config")
    parser.add_argument("method_config")
    parser.add_argument("save_path")
    parser.add_argument("log_path", nargs="?", default="log")
    parser.add_argument("parallel", nargs="?", default="False")

    args = parser.parse_args()
    election_config = args.election_config
    method_config = args.method_config
    save_path = args.save_path
    log_path = args.log_path
    parallel = eval(args.parallel)
    print(election_config, method_config, save_path, log_path, parallel)

    assert method_config.endswith(".csv")
    assert election_config.endswith(".csv")
    assert save_path is not None
    run_calibration(election_config, method_config, save_path, log_path, parallel)


def run_calibration(election_config, method_config, save_path, log_path, parallel):
    election_kwargs_list, calibration_kwargs, alternative_ps = parse_election_config(election_config)

    def yield_calibrator():
        for election_kwargs in election_kwargs_list:
            print("Election kwargs:", election_kwargs)
            election = Election(**election_kwargs)

            audit_method_calibrator = AuditMethodCalibrator(election, **calibration_kwargs)

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

                    print("Method kwargs:", audit_kwargs)
                    audit_method_calibrator.add_method_config(**audit_kwargs)
            yield audit_method_calibrator, alternative_ps, save_path, log_path

    if parallel:
        n_jobs = 2
        if isinstance(parallel, int):
            n_jobs = parallel
        Parallel(n_jobs=n_jobs, pre_dispatch="n_jobs+3")(delayed(compute_single)(*args) for args in
                                                         yield_calibrator())
    else:
        for args in yield_calibrator():
            compute_single(*args)


def compute_single(audit_method_calibrator, alternative_ps, save_path, log_path="log"):
    from datetime import datetime
    import os
    from os import path
    # Construct log file
    election = audit_method_calibrator.election
    log_path = path.join(log_path, str(election))
    if not path.exists(log_path):
        os.makedirs(log_path)
    log_file = path.join(log_path, datetime.now().strftime("%Y%m%d-%H%M%S")+".log")
    with open(log_file, "w") as log_handle:
        with contextlib.redirect_stdout(log_handle) and \
             contextlib.redirect_stderr(log_handle):
            audit_method_calibrator.calibrate()
            audit_method_calibrator.generate_expected_statistics(alternative_ps, fpath=save_path)
            print("-------------------- Finished calibration data generation --------------------")
    return 1


if __name__ == "__main__":
    """
    The entry for the calibration for a method are:
    Method Name, Parameter Name, min_parameter, max_parameter, *(parameter names, values)
    """
    import logging
    logger = logging.getLogger("console_logger")
    logger.setLevel(logging.ERROR)
    main_run_calibration()
