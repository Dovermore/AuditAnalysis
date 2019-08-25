import os
import subprocess
from os import path


def benchmark(base_path="configs", base_log_path="benchmark_logs"):
    python = "/anaconda/envs/ml_env/bin/python"
    run_file = "/Users/Dovermore/Documents/Research/AustralianElectionAuditing/AuditAnalysis/python/run_calibrated_generation.py"
    for file_path, folders, files in os.walk(base_path):
        print(file_path)
        for file in files:
            if file.endswith(".csv"):
                log_path = path.join(base_log_path, file_path)
                if not path.exists(log_path):
                    os.makedirs(log_path)
                log_file = path.join(log_path, file.rsplit(".")[0]+".log")
                print(file, log_path, log_file)
                with open(log_file, "w") as log:
                    file = path.join(file_path, file)
                    print(file)
                    args = [python, run_file, file]
                    subprocess.Popen(args=args, stdout=log)


if __name__ == "__main__":
    benchmark()
