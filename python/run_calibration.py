import argparse
from calibration.calibration_data_generation import AuditMethodCalibrator
from auditing_setup.audit_methods import *
import csv
from os import path


def run_calibration():
    parser = argparse.ArgumentParser()
    parser.add_argument("file_path")
    args = parser.parse_args()
    file_path = args.file_path
    assert file_path.endswith(".csv")

    with open(file_path) as config_file:
        config_reader = csv.reader(config_file)
        global_setting = next(config_reader)
        global_parameters = ["n", "m", "risk_lim", "p_0", "step", "replacement", "tol", "max_iter", "fpath"]

        global_kwargs = dict(zip(global_parameters, global_setting))

        global_kwargs["n"] = int(global_kwargs["n"])
        global_kwargs["m"] = int(global_kwargs["m"])
        global_kwargs["fpath"] = path.join(global_kwargs["fpath"], f"election_n={global_kwargs['n']:06d}_m="
                                           f"{global_kwargs['m']:05d}_replacement={global_kwargs['replacement']}_"
                                           f"step={global_kwargs['step']}")
        if not global_kwargs["replacement"]:
            global_kwargs["replacement"] = "False"

        if not global_kwargs["step"]:
            global_kwargs["step"] = 1

        null_params = set()

        for param in global_kwargs:
            if param not in ("n", "m", "fpath") and global_kwargs[param]:
                global_kwargs[param] = eval(global_kwargs[param])
            elif not global_kwargs[param]:
                null_params.add(param)
        for param in null_params:
            del global_kwargs[param]
        print(global_kwargs)
        audit_method_calibrator = AuditMethodCalibrator(**global_kwargs)

        audit_parameters = ["audit_method", "param_name", "param_min", "param_max"]

        config_list = list(config_reader)
        for audit_setting in config_list[:-2]:
            audit_kwargs = dict(zip(audit_parameters, audit_setting[:4]))
            for key in audit_kwargs:
                if key != "param_name":
                    audit_kwargs[key] = eval(audit_kwargs[key])
            for ind in range(4, len(audit_setting), 2):
                audit_kwargs[audit_setting[ind]] = eval(audit_setting[ind + 1])
            print(audit_kwargs)
            audit_method_calibrator.add_method_config(**audit_kwargs)

        true_ps = []
        for true_p in config_list[-2]:
            true_ps.append(float(true_p))
        save = eval(config_list[-1][0])

        audit_method_calibrator.calibrate()
        audit_method_calibrator.generate_expected_statistics(true_ps, save=save)


if __name__ == "__main__":
    run_calibration()
