from audit_power import *
from audit_method import *
from multiprocessing import Process
import numpy as np

# Code for making the comparison plot
n = 500
m = 200
replacement = False
min_alpha = 0.005
max_alpha = 0.15
n_param = 20


def bayesian_computation(n=n, m=m):
    true_ps = [0.5, 0.7, 0.58, 0.52]
    fpath = join("..", "data", f"{n:06}{m:04}_{'w' if replacement else 'wo'}")
    bayesian_params = {"thresh":
                           list(np.linspace(0.9, 0.95, 3)) +
                           list(np.linspace(0.955, 0.9999, 20))}
    bayesian_auditors = {"partisan_w1": {"a": 9, "b": 1},
                         "nonpartisan": {"a": 1, "b": 1},
                         "partisan_l1": {"a": 1, "b": 9},
                         "partisan_w2": {"a": 4, "b": 1},
                         "partisan_l2": {"a": 1, "b": 4}}

    def single_bayesian_computation(a, b):
        bayesian_audit = AuditSimulation(Bayesian, n, m,
                                         replacement=replacement)
        bayesian_table, bayesian_dsample = \
            bayesian_audit.tabular_power(true_ps, bayesian_params,
                                         dsample=True, a=a, b=b)
        to_csv(bayesian_dsample,
               f"bayesian{a:02}{b:02}_dsample.csv",
               dsample=True, fpath=fpath)
        to_csv(bayesian_table,
               f"bayesian{a:02}{b:02}_table.csv", fpath=fpath)

    for partisan in bayesian_auditors:
        a = bayesian_auditors[partisan]["a"]
        b = bayesian_auditors[partisan]["b"]
        sub_process = Process(target=single_bayesian_computation, args=(a, b))
        sub_process.start()


def clip_computation(n=n, m=m):
    true_ps = [0.5, 0.7, 0.58, 0.52]
    fpath = join("..", "data", f"{n:06}{m:04}_{'w' if replacement else 'wo'}")
    # Clip auditing
    clip_params = {"alpha": list(np.linspace(min_alpha,
                                             max_alpha, n_param))}
    clip_audit = AuditSimulation(Clip, n, m, replacement=replacement)
    clip_table, clip_dsample = \
        clip_audit.tabular_power(true_ps, clip_params, dsample=True,
                                 conservative=True, n=n)
    to_csv(clip_dsample, f"clip_dsample.csv", dsample=True, fpath=fpath)
    to_csv(clip_table, f"clip_table.csv", fpath=fpath)


def bravo_computation(n=n, m=m):
    # BRAVO auditing
    # Reset True P
    true_ps = [0.7, 0.58, 0.52]
    fpath = join("..", "data", f"{n:06}{m:04}_{'w' if replacement else 'wo'}")
    bravo_params = {"alpha": list(np.linspace(min_alpha,
                                              max_alpha, n_param))}

    def single_bravo_computation(reported):
        bravo = AuditSimulation(BRAVO, n, m, replacement=replacement)
        bravo_dsample = []
        bravo_power_table = pd.DataFrame()
        bravo_type1_table = pd.DataFrame()
        for true_p in true_ps:
            power, dsample = bravo.powers(true_p, bravo_params,
                                          progression=False,
                                          dsample=True, p=reported)
            bravo_dsample.append(dsample)
            type1 = bravo.powers(0.5, bravo_params, p=reported)
            # bravo_args.append(f"bravo_{true_p}")
            # bravo_args.append(type1)
            bravo_type1_table[true_p] = type1
            # bravo_args.append(power)
            bravo_power_table[true_p] = power
        bravo_dsample: pd.DataFrame = pd.concat(bravo_dsample,
                                                keys=true_ps, axis=0)
        to_csv(bravo_dsample,
               f"bravo{reported*100:03.0f}_dsample.csv",
               dsample=True, fpath=fpath)
        to_csv(bravo_type1_table,
               f"bravo{reported*100:03.0f}_type1.csv", fpath=fpath)
        to_csv(bravo_power_table,
               f"bravo{reported*100:03.0f}_power.csv", fpath=fpath)

    for reported in true_ps:
        sub_process = Process(target=single_bravo_computation,
                              args=(reported,))
        sub_process.start()


if __name__ == "__main__":
    bayesian_output = True
    clip_output = True
    bravo_output = True

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
        bravo_p = Process(target=bravo_computation)
        bravo_p.start()

    # dict_args = split_args(bravo_args+bayesian_args+clip_args)
    #
    # figure = plt.figure(figsize=[20.48, 20.48])
    # ncol = ceil(np.sqrt(len(true_ps)))
    # nrow = ceil(len(true_ps)/ncol)
    # i = 1
    # for true_p, args in sorted(dict_args.items(), key=lambda x: x[1]):
    #     if true_p == 0.5:
    #         continue
    #     args = [i for triples in args for i in triples]
    #     plt.subplot(nrow, ncol, i)
    #     type1_power_plot(*args)
    #     plt.title(f"p={true_p}")
    #     # Limit it to certain degree
    #     plt.xlim([0, max_alpha])
    #     i += 1
    # save_fig(f"overall_plot_{n}_{m}.png")
    # figure.show()

    # fig = type1_power_plot(*bravo_args)
    # fig.show()
