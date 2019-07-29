from auditing_setup.audit_power import *
from auditing_setup.audit_method import *
from multiprocessing import Process
import numpy as np

# Code for making the comparison plot
n = 500
m = -1
replacement = False
min_alpha = 0.005
max_alpha = 0.15
n_param = 40
true_p = 0.5
fpath = join("..", "new_data", f"{n:06}{m:04}{true_p*100:03.0f}_{'w' if replacement else 'wo'}")

def bayesian_computation(n=n, m=m, true_p=true_p, fpath=fpath):

    bayesian_params = {"thresh":
                           list(np.linspace(0.9, 0.95, 3)) +
                           list(np.linspace(0.955, 0.9999, 30))}
    # bayesian_auditors = {"partisan_w1": {"a": 9, "b": 1},
    #                      "nonpartisan": {"a": 1, "b": 1},
    #                      "partisan_l1": {"a": 1, "b": 9},
    #                      "partisan_w2": {"a": 4, "b": 1},
    #                      "partisan_l2": {"a": 1, "b": 4}}

    bayesian_auditors = {"nonpartisan": {"a": 1, "b": 1}}

    def single_bayesian_computation(a, b):
        bayesian_audit = AuditSimulation(Bayesian, n, m, replacement=replacement)
        bayesian_table, bayesian_dsample = bayesian_audit.powers(true_p, bayesian_params, dsample=True, cdf=True, a=a, b=b)
        to_csv(bayesian_dsample, f"bayesian{a:02}{b:02}_cdf.csv", fpath=fpath)

    for partisan in bayesian_auditors:
        a = bayesian_auditors[partisan]["a"]
        b = bayesian_auditors[partisan]["b"]
        sub_process = Process(target=single_bayesian_computation, args=(a, b))
        sub_process.start()


def clip_computation(n=n, m=m, true_p=true_p, fpath=fpath):
    # Clip auditing
    clip_params = {"alpha": list(np.linspace(min_alpha, max_alpha, n_param))}
    clip_audit = AuditSimulation(Clip, n, m, replacement=replacement)
    clip_table, clip_dsample = clip_audit.powers(true_p, clip_params, dsample=True, cdf=True, conservative=True, n=n)
    to_csv(clip_dsample, f"clip_cdf.csv", fpath=fpath)


def hyper_geom_bravo_computation(n=n, m=m, true_p=true_p, fpath=fpath):
    reported_ps = [0.55, 0.7]
    bravo_params = {"alpha": list(np.linspace(min_alpha, max_alpha, n_param))}

    def single_bravo_computation(reported):
        bravo = AuditSimulation(HyperGeomBRAVO, n, m, replacement=replacement)
        power, dsample = bravo.powers(true_p, bravo_params, progression=False, dsample=True, cdf=True, p=reported)
        to_csv(dsample, f"bravo{reported*100:03.0f}_cdf.csv", fpath=fpath)

    for reported in reported_ps:
        sub_process = Process(target=single_bravo_computation,
                              args=(reported,))
        sub_process.start()


def truncated_bayesian_computation(n=n, m=m, true_p=true_p, fpath=fpath):
    bayesian_params = {"thresh": list(np.linspace(min_alpha, max_alpha, n_param))}

    bayesian_auditors = {"nonpartisan": {"a": 1, "b": 1}}

    # bayesian_auditors = {"partisan_w1": {"a": 9, "b": 1},
    #                      "nonpartisan": {"a": 1, "b": 1},
    #                      "partisan_l1": {"a": 1, "b": 9},
    #                      "partisan_w2": {"a": 4, "b": 1},
    #                      "partisan_l2": {"a": 1, "b": 4}}

    # bayesian_auditors = {"partisan_w1": {"a": 9, "b": 1},
    #                      "nonpartisan": {"a": 1, "b": 1},
    #                      "partisan_l1": {"a": 1, "b": 9},
    #                      "partisan_w2": {"a": 4, "b": 1},
    #                      "partisan_l2": {"a": 1, "b": 4}}

    def single_bayesian_computation(a, b):
        bayesian_audit = AuditSimulation(TruncatedBayesian, n, m, replacement=replacement)
        bayesian_table, bayesian_dsample = bayesian_audit.powers(true_p, bayesian_params, dsample=True,
                                                                 cdf=True, a=a, b=b)
        to_csv(bayesian_dsample, f"{TruncatedBayesian.name}{a:02}{b:02}_cdf.csv", fpath=fpath)

    for partisan in bayesian_auditors:
        a = bayesian_auditors[partisan]["a"]
        b = bayesian_auditors[partisan]["b"]
        sub_process = Process(target=single_bayesian_computation, args=(a, b))
        sub_process.start()


if __name__ == "__main__":
    bayesian_output = False
    clip_output = False
    bravo_output = False
    truncated_bayesian_output = True

    # Bayesian auditing
    if bayesian_output:
        bayesian_p = Process(target=bayesian_computation)
        bayesian_p.start()

    # Clip auditing
    if clip_output:
        clip_p = Process(target=clip_computation)
        clip_p.start()

    # BRAVO auditing
    if bravo_output:
        bravo_p = Process(target=hyper_geom_bravo_computation)
        bravo_p.start()

    # Bayesian auditing
    if truncated_bayesian_output:
        truncated_bayesian_p = Process(target=truncated_bayesian_computation)
        truncated_bayesian_p.start()
