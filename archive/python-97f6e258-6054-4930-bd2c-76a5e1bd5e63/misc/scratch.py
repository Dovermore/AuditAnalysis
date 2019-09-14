from auditing_setup.raw_distributions import *
from auditing_setup.audit_methods import *
from auditing_setup.expected_statistics import *

audit_s = AuditMethodDistributionComputer(TruncatedBayesian, 500, 500)
# audit_s.power(0.7)
