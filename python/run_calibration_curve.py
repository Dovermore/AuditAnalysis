import argparse
import csv

# The following import is needed because `eval` is used for audit methods
from os import path

from auditing_setup.audit_methods import *
from calibration.calibration_curve_generator import CalibrationCurveGenerator
from calibration.calibration_data_generation import AuditMethodCalibrator

from parse_election import parse_election_config


def main_run_calibration_curve():
    parser = argparse.ArgumentParser()
    parser.add_argument("election_config")
    parser.add_argument("method_config")

    args = parser.parse_args()
    election_config = args.election_config
    method_config = args.method_config

    assert method_config.endswith(".csv")
    assert election_config.endswith(".csv")
    run_calibration(election_config, method_config)


def run_calibration(election_config, method_config):
    global_kwargs, true_ps, save = parse_election_config(election_config)
    for key in ("tol", "max_iter", "fpath", "risk_lim"):
        if key in global_kwargs:
            global_kwargs.pop(key)
    global_kwargs["fpath"] = "calibration_curve"
    audit_method_calibrator = CalibrationCurveGenerator(**global_kwargs)

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

            print(audit_kwargs)
            audit_method_calibrator.compute_curve(**audit_kwargs)


if __name__ == "__main__":
    """
    The entry for the calibration for a method are:
    Method Name, Parameter Name, min_parameter, max_parameter, *(parameter names, values)
    """
    import logging
    logger = logging.getLogger("console_logger")
    logger.setLevel(logging.ERROR)

    main_run_calibration_curve()
