from auditing_setup.raw_distributions import *
from auditing_setup.audit_methods import *
from multiprocessing import Process
import numpy as np

# Code for making the comparison plot
n = 500
m = -1
replacement = False
min_alpha = 0.005
max_alpha = 0.15
n_param = 40
p_0 = 0.5
fpath = join("..", "new_data", f"{n:06}{m:04}{p_0 * 100:03.0f}_{'w' if replacement else 'wo'}")


def bayesian_computation(n=n, m=m, p_0=p_0, fpath=fpath):

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
        bayesian_audit = AuditMethodDistributionComputer(Bayesian, n, m, replacement=replacement)
        bayesian_table, bayesian_dsample = bayesian_audit.powers(p_0, bayesian_params, dsample=True, cdf=True, a=a, b=b)
        to_csv(bayesian_dsample, f"bayesian{a:02}{b:02}_cdf.csv", fpath=fpath)

    for partisan in bayesian_auditors:
        a = bayesian_auditors[partisan]["a"]
        b = bayesian_auditors[partisan]["b"]
        sub_process = Process(target=single_bayesian_computation, args=(a, b))
        sub_process.start()


def clip_computation(n=n, m=m, p_0=p_0, fpath=fpath):
    # Clip auditing
    clip_params = {"alpha": list(np.linspace(min_alpha, max_alpha, n_param))}
    clip_audit = AuditMethodDistributionComputer(Clip, n, m, replacement=replacement)
    clip_table, clip_dsample = clip_audit.powers(p_0, clip_params, dsample=True, cdf=True, conservative=True, n=n)
    to_csv(clip_dsample, f"clip_cdf.csv", fpath=fpath)


def hyper_geom_bravo_computation(n=n, m=m, p_0=p_0, fpath=fpath):
    reported_ps = [0.55, 0.7]
    bravo_params = {"alpha": list(np.linspace(min_alpha, max_alpha, n_param))}

    def single_bravo_computation(reported):
        bravo = AuditMethodDistributionComputer(HyperGeomBRAVO, n, m, replacement=replacement)
        power, dsample = bravo.powers(p_0, bravo_params, progression=False, dsample=True, cdf=True, p=reported)
        to_csv(dsample, f"bravo{reported*100:03.0f}_cdf.csv", fpath=fpath)

    for reported in reported_ps:
        sub_process = Process(target=single_bravo_computation,
                              args=(reported,))
        sub_process.start()


def max_sprt_computation(n=n, m=m, p_0=p_0, fpath=fpath):
    sprt_params = {"alpha": list(np.linspace(min_alpha, max_alpha, n_param//3))}
    max_sprt = AuditMethodDistributionComputer(MaxSPRT, n, m, replacement=replacement)
    power, dsample = max_sprt.powers(p_0, sprt_params, progression=False, dsample=True, cdf=True, auto_max_sample=m if m > 0 else n)
    to_csv(dsample, f"max_sprt_cdf.csv", fpath=fpath)


def truncated_bayesian_computation(n=n, m=m, p_0=p_0, fpath=fpath):
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
        bayesian_audit = AuditMethodDistributionComputer(TruncatedBayesian, n, m, replacement=replacement)
        bayesian_table, bayesian_dsample = bayesian_audit.powers(p_0, bayesian_params, dsample=True,
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
    truncated_bayesian_output = False
    sprt_output = True

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

    # Bayesian auditing
    if sprt_output:
        max_sprt_p = Process(target=max_sprt_computation)
        max_sprt_p.start()
