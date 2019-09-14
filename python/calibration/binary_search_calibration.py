from auditing_setup.audit_methods import *
from auditing_setup.raw_distributions import *
from auditing_setup.election_setting import Election
from copy import deepcopy


class RiskOutOfRangeError(ValueError):
    pass


class RiskBinarySearch:
    """
    A class that implements binary search to calibrate certain parameter for a given risk limit
    """

    def __init__(self, audit_method, param_name, param_min, param_max, election: Election, tol=1e-3, max_iter=40, **kwargs):
        self.audit_method = audit_method
        self.param_name = param_name
        self.param_min = param_min
        self.param_max = param_max
        self.election = election
        self.kwargs = kwargs
        self.risk_lim = None
        self.tol = tol
        self.step_count = 0
        self.max_iter = max_iter
        self.method_distribution_computer = AuditMethodDistributionComputer(audit_method)
        self.reset()

    def reset(self):
        self.prev_param_val = None
        self.prev_param_risk = None
        self.param_val = self.param_min
        self.param_risk = None
        self.increasing_risk = None
        self.lo = None
        self.hi = None
        self._search_record = {}

    def __next__(self, detail=True):
        """
        Carries out a single step of computation and output parameter and risk in a dictionary

        Uses the knowledge that parameters in audit are almost all monotonically related to risk
        """
        self.step_count += 1

        full_kwargs = deepcopy(self.kwargs)
        full_kwargs[self.param_name] = self.param_val

        # TODO separate audit process related things out
        self.param_risk = self.method_distribution_computer.power(self.election, **full_kwargs)
        self._search_record[self.param_val] = self.param_risk

        print("{} -> {} | {} | {}".format(self.param_val, self.param_risk, self.lo, self.hi))

        ret = False
        if self.param_risk < self.risk_lim and self.risk_lim - self.param_risk < self.tol:
            ret = True
        else:
            if self.increasing_risk is None and self.prev_param_val is None:
                self.prev_param_val = self.param_val
                self.prev_param_risk = self.param_risk
                self.param_val = self.param_max
            else:
                if self.increasing_risk is None:
                    self.increasing_risk = self.prev_param_risk < self.param_risk
                    min_risk = min(self.prev_param_risk, self.param_risk)
                    max_risk = max(self.prev_param_risk, self.param_risk)
                    if not min_risk <= self.risk_lim <= max_risk:
                        raise RiskOutOfRangeError("Risk Lim {:.5f} is not in the "
                                                  "range of possible risks {:.5f} <= risk <= {:.5f}\n"
                                                  "audit_method: {}, kwargs: {}, "
                                                  "param:{}_{},{}, \n"
                                                  "{}".format(self.risk_lim, min_risk, max_risk, self.audit_method.name, full_kwargs, self.param_name, self.param_min, self.param_max, self.election))
                    self.lo = self.param_min if self.increasing_risk else self.param_max
                    self.hi = self.param_max if self.increasing_risk else self.param_min
                self.prev_param_val = self.param_val
                self.prev_param_risk = self.param_risk
                if self.param_risk < self.risk_lim:
                    self.lo = self.param_val
                    self.param_val = (self.hi + self.param_val) / 2
                else:
                    self.hi = self.param_val
                    self.param_val = (self.lo + self.param_val) / 2
        return (ret, self.param_risk) if detail else ret

    def binary_search(self, risk_lim=0.05, manual=False, just_warn=True):
        self.risk_lim = risk_lim
        self.reset()

        try:
            while self.__next__(detail=False) is not True:
                if len(self._search_record.values()) != len(set(self._search_record.values())):
                    print("Repeated Risk found when searching, stop searching now...")
                    break
                if self.step_count >= self.max_iter:
                    print("Maximum iter reached {}".format(self.max_iter))
                    if manual:
                        user_input = input("please enter a new number of max iteration (> {}) or 'n' to terminate:\n".format(self.max_iter))
                        if user_input == "n" or int(user_input) < self.max_iter:
                            break
                        else:
                            self.max_iter = int(user_input)
                    else:
                        break
        except RiskOutOfRangeError as rooe:
            if just_warn:
                from sys import stderr
                print("--------------------", file=stderr)
                print(rooe, file=stderr)
                print("No appropriate risk found, using {}={}, with risk: {} instead".format(self.param_name, self.param_val, self.param_risk), file=stderr)
                print("--------------------", file=stderr)
            elif not manual:
                raise StopIteration("Error Encountered in available range of risks")
            else:
                new_min = input("Enter a new minimum for the parameter({}), enter 'n' to cancel".format(self.param_name))
                if new_min == "n":
                    return
                self.param_min = float(new_min)
                new_max = input("Enter a new maximum for the parameter({}), enter 'n' to cancel".format(self.param_name))
                if new_max == "n":
                    return
                self.param_max = float(new_max)
                return self.binary_search(risk_lim)
        return self.param_val, self.param_risk

    @property
    def search_record(self):
        return pd.Series(self._search_record)


if __name__ == "__main__":
    audit_method = MaxSPRT
    rbs = RiskBinarySearch(audit_method, "alpha", 0.01, 0.2, 100, 100)
    print(rbs.binary_search())
    print(rbs.search_record)
