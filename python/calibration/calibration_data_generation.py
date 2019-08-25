from auditing_setup.expected_statistics import audit_method_expected_statistics
from .binary_search_calibration import RiskBinarySearch
from os import path
from copy import deepcopy


class AuditMethodCalibrator:
    """
    This class is responsible for calibrating different auditing methodologies and output some unified data for
    further analysis
    """

    def __init__(self, n, m, risk_lim=0.05, p_0=0.5, step=1, replacement=False, tol=1e-3,
                 max_iter=40, fpath="calibrated_data"):
        """
        Initialise the class with a default risk limit
        :param risk_lim: risk limit
        """
        self.n = n
        self.m = m
        self.p_0 = p_0
        self.step = step
        self.replacement = replacement
        self.audit_methods = {}
        self.risk_lim = risk_lim
        self.fpath = fpath
        self.tol = tol
        self.max_iter = max_iter

    def add_method_config(self, audit_method, param_name, param_min, param_max, **kwargs):
        if audit_method not in self.audit_methods:
            self.audit_methods[audit_method] = {
                "risk_search": [],
                "calibrated_risk": [],
                "calibrated_param_val": [],
                "calibration_record": [],
                "calibrated_param_expected_statistics": None,
            }
        audit_method_dict = self.audit_methods[audit_method]
        audit_method_dict["risk_search"].append(RiskBinarySearch(audit_method, param_name, param_min, param_max,
                                                                 self.n, self.m, self.p_0, self.step, self.replacement,
                                                                 self.tol, self.max_iter, **kwargs))

    def remove_method(self, audit_method):
        try:
            del self.audit_methods[audit_method]
        finally:
            pass

    def calibrate(self, manual=False):
        self.reset()
        for audit_method in self.audit_methods:
            audit_method_dict = self.audit_methods[audit_method]
            for risk_calibrator in audit_method_dict["risk_search"]:
                print(f"---- {audit_method.name}({risk_calibrator.param_name}, kwargs: {risk_calibrator.kwargs}) ----")
                calibrated_param_val, calibrated_risk = risk_calibrator.binary_search(self.risk_lim, manual=manual)
                audit_method_dict["calibrated_risk"].append(calibrated_risk)
                audit_method_dict["calibrated_param_val"].append(calibrated_param_val)
                audit_method_dict["calibration_record"].append(risk_calibrator.search_record)

    def reset(self):
        for audit_method in self.audit_methods:
            audit_method_dict = self.audit_methods[audit_method]
            audit_method_dict["calibrated_risk"] = []
            audit_method_dict["calibrated_param_val"] = []
            audit_method_dict["calibration_record"] = []
            audit_method_dict["calibrated_param_expected_statistics"] = []
            for risk_calibrator in audit_method_dict["risk_search"]:
                risk_calibrator.reset()

    def generate_expected_statistics(self, true_ps, save=True):
        for audit_method in self.audit_methods:
            audit_method_dict = self.audit_methods[audit_method]
            assert audit_method_dict["calibrated_param_val"] is not None
            kwargs_list = []
            for setting_ind in range(len(audit_method_dict["risk_search"])):
                risk_calibrator = audit_method_dict["risk_search"][setting_ind]
                kwargs = deepcopy(risk_calibrator.kwargs)
                kwargs[risk_calibrator.param_name] = audit_method_dict["calibrated_param_val"][setting_ind]
                kwargs_list.append(kwargs)
            audit_method_dict["calibrated_param_expected_statistics"] = \
                audit_method_expected_statistics(audit_method, kwargs_list, self.n, self.m, step=self.step,
                                                 replacement=self.replacement, true_ps=true_ps, save=save,
                                                 fpath=path.join(self.fpath, f"{audit_method.name}_{self.risk_lim}"))
