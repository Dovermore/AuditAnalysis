from auditing_setup.expected_statistics import audit_method_expected_statistics
from auditing_setup.election_setting import Election
from .binary_search_calibration import RiskBinarySearch
from os import path
from copy import deepcopy


class AuditMethodCalibrator:
    """
    This class is responsible for calibrating different auditing methodologies and output some unified data for
    further analysis
    """

    def __init__(self, election: Election, risk_lim=0.05, **calibration_kwargs):
        """
        Initialise the class with a default risk limit
        :param risk_lim: risk limit
        """
        self.election = election
        self.audit_methods = {}
        self.risk_lim = risk_lim
        self.calibration_kwargs = calibration_kwargs

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
                                                                 self.election, **kwargs, **self.calibration_kwargs))

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

    def generate_expected_statistics(self, true_ps, fpath="calibrated_data"):
        fpath = path.join(fpath, str(self.election))

        for audit_method in self.audit_methods:
            audit_method_dict = self.audit_methods[audit_method]
            assert audit_method_dict["calibrated_param_val"] is not None
            kwargs_list = []

            elections = [self.election.clone() for _ in true_ps]
            for election, true_p in zip(elections, true_ps):
                election.p = true_p
            elections.insert(0, self.election)

            for setting_ind in range(len(audit_method_dict["risk_search"])):
                risk_calibrator = audit_method_dict["risk_search"][setting_ind]
                kwargs = deepcopy(risk_calibrator.kwargs)
                kwargs[risk_calibrator.param_name] = audit_method_dict["calibrated_param_val"][setting_ind]
                kwargs_list.append(kwargs)
            audit_method_dict["calibrated_param_expected_statistics"] = \
                audit_method_expected_statistics(audit_method, kwargs_list, elections,
                                                 fpath=path.join(fpath, f"{audit_method.name}_{self.risk_lim}"))
