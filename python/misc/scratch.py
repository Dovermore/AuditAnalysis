from auditing_setup.audit_power import *
from auditing_setup.audit_method import *
from auditing_setup.audit_sample_number_analysis import *

audit_s = AuditSimulation(TruncatedBayesian, 500, 500)
audit_s.power(0.7)
