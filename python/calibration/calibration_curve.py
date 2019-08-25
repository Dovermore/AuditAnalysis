from auditing_setup.audit_methods import *
from auditing_setup.raw_distributions import AuditMethodDistributionComputer
from copy import deepcopy
import pandas as pd
import numpy as np


class CalibrationCurve:
    def __init__(self, audit_method, param_name, param_min, param_max, n=500, m=500, p_0=0.5, step=1,
                 replacement=False, tol=1e-3, max_iter=40, **kwargs):
        self.audit_method = audit_method
        self.param_name = param_name
        self.param_min = param_min
        self.param_max = param_max
        self.kwargs = kwargs
        self.p_0 = p_0
        self.step = step
        self.replacement = replacement
        self.risk_lim = None
        self.n = n
        self.m = m
        self.tol = tol
        self.max_iter = max_iter
        self.method_distribution_computer = AuditMethodDistributionComputer(audit_method, n, m, step=step,
                                                                            replacement=replacement)
        self._search_record = {}

    def compute_curve(self):
        for param_val in np.linspace(self.param_min, self.param_max, num=self.max_iter):
            kwargs = deepcopy(self.kwargs)
            kwargs[self.param_name] = param_val
            self._search_record[param_val] = self.method_distribution_computer.power(true_p=self.p_0, dsample=False,
                                                                                     **kwargs)
        return pd.Series(data=self._search_record, name=f"{self.audit_method.name}-{self.param_name}-search").sort_index()


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

    kwargs = {
        "audit_method": Bayesian,
        "param_name": "critical_value",
        "param_min": 0.0000000001,
        "param_max": 0.02,
        "n": 1000,
        "m": 100,
        "step": 1,
        "replacement": False,
        "a": 1,
        "b": 1,
        "multiprocessing": False
    }

    cc = CalibrationCurve(**kwargs)
    curve = cc.compute_curve()

    import matplotlib.pyplot as plt
    plt.plot(curve)
    plt.show()

