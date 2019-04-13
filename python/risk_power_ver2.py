from auditing_power import *


if __name__ == "__main__":
    # Sanity check for bravo auditing
    # bravo_check(n=10000, m=500)

    # Sanity check for bayesian auditing
    # bayesian_check(n=10000)

    # Sanity Check for Clip auditing
    # clip_check()

    # Code for making the comparison plot
    # n = 20000
    # m = 500
    n = 10000
    m = 200
    min_alpha = 0.005
    max_alpha = 0.15
    n_param = 15
    fpath = join("..", "data", f"_normal")

    # true_ps = [0.7, 0.65, 0.6, 0.58, 0.55, 0.54, 0.53, 0.52, 0.51, 0.505]
    true_ps = [0.5, 0.7, 0.58, 0.52]
    # true_ps = [0.5, 0.7, 0.6, 0.55, 0.52]

    bayesian_output = True
    clip_output = True
    bravo_output = True

    # Bayesian auditing
    if bayesian_output:
        bayesian_params = {"thresh":
                           list(np.linspace(0.9, 0.95, 3)) +
                           list(np.linspace(0.955, 0.9999, 20))}
        bayesian_auditors = {"partisan_w1": {"a": 9, "b": 1},
                             "nonpartisan": {"a": 1, "b": 1},
                             "partisan_l1": {"a": 1, "b": 9},
                             "partisan_w2": {"a": 4, "b": 1},
                             "partisan_l2": {"a": 1, "b": 4}}
        # TODO add plot using dictionary
        bayesian_audit = AuditSimulation(Bayesian, n, m)
        for partisan in bayesian_auditors:
            a = bayesian_auditors[partisan]["a"]
            b = bayesian_auditors[partisan]["b"]
            bayesian_table, bayesian_dsample = \
                bayesian_audit.tabular_power(true_ps, bayesian_params,
                                             dsample=True, a=a, b=b)
            to_csv(bayesian_dsample,
                   f"bayesian_dsample{a:02}{b:02}.csv",
                   dsample=True, fpath=fpath)
            to_csv(bayesian_table,
                   f"bayesian_table{a:02}{b:02}.csv", fpath=fpath)
        # bayesian_args = parse_table(bayesian_table, "bayesian")

    # Clip auditing
    if clip_output:
        clip_params = {"alpha": list(np.linspace(min_alpha,
                                                 max_alpha, n_param))}
        clip_audit = AuditSimulation(Clip, n, m)
        clip_table, clip_dsample = \
            clip_audit.tabular_power(true_ps, clip_params, dsample=True,
                                     conservative=True, n=n)
        to_csv(clip_dsample, f"clip_dsample.csv", dsample=True,
               fpath=fpath)
        to_csv(clip_table, f"clip_table.csv", fpath=fpath)
        clip_args = parse_table(clip_table, "clip")

    # BRAVO auditing
    if bravo_output:
        # Reset True P
        true_ps = [0.7, 0.58, 0.52]
        bravo_params = {"alpha": list(np.linspace(min_alpha,
                                                  max_alpha, n_param))}
        bravo = AuditSimulation(BRAVO, n, m)
        for reported in true_ps:
            bravo_args = []
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
                   f"bravo_dsample{reported*100:03.0f}.csv",
                   dsample=True, fpath=fpath)
            to_csv(bravo_type1_table,
                   f"bravo_type1{reported*100:03.0f}.csv",
                   fpath=fpath)
            to_csv(bravo_power_table,
                   f"bravo_power{reported*100:03.0f}.csv",
                   fpath=fpath)

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
