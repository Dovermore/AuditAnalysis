import csv
from os import path


def parse_election_config(election_config):
    with open(election_config) as config_file:
        config_reader = csv.reader(config_file)
        global_setting = next(config_reader)
        global_parameters = ["n", "m", "risk_lim", "p_0", "step", "replacement", "tol", "max_iter"]

        global_kwargs = dict(zip(global_parameters, global_setting))

        global_kwargs["n"] = int(global_kwargs["n"])
        global_kwargs["m"] = int(global_kwargs["m"])
        if not global_kwargs["replacement"]:
            global_kwargs["replacement"] = "False"

        if not global_kwargs["step"]:
            global_kwargs["step"] = 1

        null_params = set()

        for param in global_kwargs:
            if param not in ("n", "m") and global_kwargs[param]:
                global_kwargs[param] = eval(global_kwargs[param])
            elif not global_kwargs[param]:
                null_params.add(param)
        for param in null_params:
            del global_kwargs[param]

        true_ps = []
        for true_p in next(config_reader):
            true_ps.append(float(true_p))
        save_config = next(config_reader)
        save = eval(save_config[0])
        if save:
            global_kwargs["fpath"] = save_config[1]
        global_kwargs["fpath"] = path.join(global_kwargs["fpath"], f"election_n={global_kwargs['n']:06d}_m="
                                                                   f"{global_kwargs['m']:05d}_replacement={global_kwargs['replacement']}_"
                                                                   f"step={global_kwargs['step']}")
        print(global_kwargs)
        return global_kwargs, true_ps, save

