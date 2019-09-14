import os
import subprocess
from os import path


def benchmark():
    os.environ["R_HOME"] = "/Users/Dovermore/.conda/envs/audit_analysis/lib/R"
    python = "/Users/Dovermore/.conda/envs/audit_analysis/bin/python"
    project_base = "/Users/Dovermore/Documents/Research/AustralianElectionAuditing/AuditAnalysis.nosync"

    calibrated_script = path.join(project_base, "python", "run_calibrated_generation.py")
    assert path.exists(calibrated_script), calibrated_script
    uncalibrated_script = path.join(project_base, "python", "run_uncalibrated_generation.py")
    assert path.exists(uncalibrated_script), uncalibrated_script
    calibration_curve_script = path.join(project_base, "python", "run_calibration_curve.py")
    assert path.exists(calibration_curve_script), calibration_curve_script

    election_config_prefix = path.join(project_base, "configs", "election_config")
    method_config_prefix = path.join(project_base, "configs", "method_config")

    # Jobs requires calibration
    calibrated_jobs = []

    # Step with n = 500
    n = 500

    step = 100
    calibrated_jobs.append([
        path.join(election_config_prefix, "step", f"election_n={n:06d}_m=00500_replacement=False_step={step}.csv"),
        path.join(method_config_prefix, "calibrated_config", f"calibration_{n:06d}.csv")
    ])

    step = 250
    calibrated_jobs.append([
        path.join(election_config_prefix, "step", f"election_n={n:06d}_m=00500_replacement=False_step={step}.csv"),
        path.join(method_config_prefix, "calibrated_config", f"calibration_{n:06d}.csv")
    ])

    # Step with n = 5000
    n = 5000

    step = 250
    calibrated_jobs.append([
        path.join(election_config_prefix, "step", f"election_n={n:06d}_m=00500_replacement=False_step={step}.csv"),
        path.join(method_config_prefix, "calibrated_config", f"calibration_{n:06d}.csv")
    ])

    step = 500
    calibrated_jobs.append([
        path.join(election_config_prefix, "step", f"election_n={n:06d}_m=00500_replacement=False_step={step}.csv"),
        path.join(method_config_prefix, "calibrated_config", f"calibration_{n:06d}.csv")
    ])

    # Step with n = 20000
    n = 20000

    step = 500
    calibrated_jobs.append([
        path.join(election_config_prefix, "step", f"election_n={n:06d}_m=02000_replacement=False_step={step}.csv"),
        path.join(method_config_prefix, "calibrated_config", f"calibration_{n:06d}.csv")
    ])
    step = 1000
    calibrated_jobs.append([
        path.join(election_config_prefix, "step", f"election_n={n:06d}_m=02000_replacement=False_step={step}.csv"),
        path.join(method_config_prefix, "calibrated_config", f"calibration_{n:06d}.csv")
    ])
    step = 2000
    calibrated_jobs.append([
        path.join(election_config_prefix, "step", f"election_n={n:06d}_m=02000_replacement=False_step={step}.csv"),
        path.join(method_config_prefix, "calibrated_config", f"calibration_{n:06d}.csv")
    ])

    for f1, f2 in calibrated_jobs:
        assert path.exists(f1), f1
        assert path.exists(f2), f2

    all_job_args = {}

    for election_config, method_config in calibrated_jobs:
        election_config_base = path.basename(election_config).replace(".csv", "")
        method_config_base = path.basename(method_config).replace(".csv", "")
        all_job_args[path.join("calibrated_log", election_config_base, method_config_base)] = [python, calibrated_script, election_config, method_config]

    from datetime import datetime
    from multiprocessing.pool import ThreadPool

    results = []

    import multiprocessing
    pool = ThreadPool(multiprocessing.cpu_count())
    # pool = ThreadPool()

    for log_path, job_args in all_job_args.items():
        log_path = path.join("log", log_path)
        if not path.exists(log_path):
            os.makedirs(log_path)
        log_file = path.join(log_path, datetime.now().strftime("%Y%m%d-%H%M%S")+".log")
        print(log_path, log_file)
        with open(log_file, "w") as log:
            results.append(pool.apply_async(call_proc, (job_args, log)))
            subprocess.Popen(args=job_args, stdout=log)

    # Close the pool and wait for each running task to complete
    pool.close()
    pool.join()
    for result in results:
        # out, err = result.get()
        # print("out: {} err: {}".format(out, err))
        pass


def call_proc(job_args, log):
    """ This runs in a separate thread. """
    p = subprocess.Popen(args=job_args, stdout=log, stderr=log)
    # out, err = p.communicate()
    # return (out, err)


if __name__ == "__main__":
    benchmark()
