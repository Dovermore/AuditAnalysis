from auditing_setup.audit_methods import *
from auditing_setup.raw_distributions import AuditMethodDistributionComputer, to_csv
from copy import deepcopy
import pandas as pd
import numpy as np


class CalibrationCurveGenerator:

    def __init__(self, election, max_iter=40, fpath="calibration_curve"):
        self.election = election
        self.audit_methods = {}
        self.fpath = fpath
        self.max_iter = max_iter

    def compute_curve(self, audit_method, param_name, param_min, param_max, save=True, **kwargs):
        search_record = {}
        method_distribution_computer = AuditMethodDistributionComputer(audit_method)
        for param_val in np.linspace(param_min, param_max, num=self.max_iter):
            kwargs = deepcopy(kwargs)
            kwargs[param_name] = param_val
            search_record[param_val] = method_distribution_computer.power(self.election, dsample=False, **kwargs)
        series = pd.Series(data=search_record, name="{}-{}-search".format(audit_method.name, param_name)).sort_index()
        if save:
            to_csv(series, "{}_curve.csv".format(make_legend(audit_method, **kwargs)
                                                 .replace(" ", "")
                                                 .replace("|", "_")), self.fpath)
        return pd.Series(data=search_record, name="{}-{}-search".format(audit_method.name, param_name)).sort_index()


if __name__ == "__main__":
    import logging
    logger = logging.getLogger("console_logger")
    logger.setLevel(logging.ERROR)
    n = 1000
    m = 500
    max_iter = 40

    audit_method = Bayesian
    param_name = "critical_value"
    param_min = 0.95
    param_max = 9.999999999

    curve_kwargs = {
        "audit_method": Bayesian,
        "param_name": "critical_value",
        "param_min": 0.0000000001,
        "param_max": 0.02,
        "a": 1,
        "b": 1,
        "multiprocessing": False
    }

    election_kwargs = {
        "n": 1000,
        "m": 100,
        "step": 1,
        "replacement": False,
    }

    cc = CalibrationCurveGenerator(**election_kwargs)
    curve = cc.compute_curve(**curve_kwargs)

    import matplotlib.pyplot as plt
    plt.plot(curve)
    plt.show()

