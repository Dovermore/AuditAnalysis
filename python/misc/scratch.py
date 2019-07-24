from auditing_setup.audit_power import *

truncated_bayesian_cdf_data = pd.read_csv("../../new_data/000500-001050_wo/truncated_bayesian0101_cdf.csv", index_col=0, header=0)
plt.plot([float(i) for i in truncated_bayesian_cdf_data.columns], truncated_bayesian_cdf_data.iloc[-1])
plt.show()