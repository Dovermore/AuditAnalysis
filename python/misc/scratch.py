from auditing_setup.audit_power import *

bayesian_dsample = pd.read_csv("../data/bayesian_dsample_1000_100.csv")



import rpy2.rinterface as ri
print('.'.join(ri.R_VERSION_BUILD[:2]))