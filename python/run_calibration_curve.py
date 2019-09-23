import argparse
import csv

from os import path

# The following import is needed because `eval` is used for audit methods
from auditing_setup.audit_methods import *
from calibration.calibration_curve_generator import CalibrationCurveGenerator

from parse_args import parse_election_config


def main_run_calibration_curve():
    parser = argparse.ArgumentParser()
    parser.add_argument("election_config")
    parser.add_argument("method_config")
    parser.add_argument("save_path", nargs="?", default="calibration_curve")
    parser.add_argument("log_path", nargs="?", default="log")
    parser.add_argument("parallel", nargs="?", default="False")

    args = parser.parse_args()
    election_config = args.election_config
    method_config = args.method_config
    save_path = args.save_path

    assert method_config.endswith(".csv")
    assert election_config.endswith(".csv")
    run_calibration(election_config, method_config, save_path)


def run_calibration(election_config, method_config, save_path="calibration_curve"):
    election_kwargs_list, calibration_kwargs, alternative_ps = parse_election_config(election_config)
    for election_kwargs in election_kwargs_list:
        print("Election kwargs:", election_kwargs)
        election = Election(**election_kwargs)
        audit_method_calibrator = CalibrationCurveGenerator(election, fpath=path.join(save_path, str(election)))
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
