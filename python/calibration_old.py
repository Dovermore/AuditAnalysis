from auditing_setup.audit_method import KMart
from auditing_setup.audit_power import AuditSimulation

if __name__ == "__main__":
    # n = 10000
    # m = 500
    # bravo_audit_simulation = AuditSimulation(BRAVO, n, m, False)
    # power = bravo_audit_simulation.power(0.50, p=0.55, alpha=0.085)
    # # 0.050
    # print(power)
    # power = bravo_audit_simulation.power(0.50, p=0.7, alpha=0.0591)
    # print(power)
    #
    # bayesian_audit_simulation = AuditSimulation(Bayesian, n, m, False)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=1, thresh=0.996322)
    # # 0.0508
    # print(power)
    # power = bayesian_audit_simulation.power(0.50, a=4, b=1, thresh=0.99902)
    # # 0.0504
    # print(power)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=4, thresh=0.9892)
    # # 0.0500
    # print(power)

    # clip_audit_simulation = AuditSimulation(Clip, n, m, False)
    # power = clip_audit_simulation.power(0.5, n=n, alpha=0.0815)
    # # 0.0505
    # print(power)


    n = 500
    m = 100
    # bravo_audit_simulation = AuditSimulation(BRAVO, n, m, False)
    # power = bravo_audit_simulation.power(0.50, p=0.55, alpha=0.25)
    # # 0.052
    # print(power)
    # power = bravo_audit_simulation.power(0.50, p=0.7, alpha=0.072)
    # # 0.052
    # print(power)

    # bravo_audit_simulation = AuditSimulation(HyperGeomBRAVO, n, m, False)
    # power = bravo_audit_simulation.power(0.50, p=0.7, alpha=0.063)
    # # 0.052
    # print(power)
    # power = bravo_audit_simulation.power(0.50, p=0.55, alpha=0.195)
    # # 0.050
    # print(power)
    #
    # bayesian_audit_simulation = AuditSimulation(Bayesian, n, m, False)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=1, thresh=0.9939)
    # # 0.052
    # print(power)
    # power = bayesian_audit_simulation.power(0.50, a=4, b=1, thresh=0.99835)
    # # 0.052
    # print(power)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=4, thresh=0.97251)
    # # 0.052
    # print(power)
    #
    # bayesian_audit_simulation = AuditSimulation(HyperGeomBayesian, n, m, False)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=1, thresh=0.99776, progression=True)
    # print(power)
    #
    # clip_audit_simulation = AuditSimulation(Clip, n, m, False)
    # power = clip_audit_simulation.power(0.5, n=n, alpha=0.075)
    # # 0.0504
    # print(power)
    #
    # kmart_audit_simulation = AuditSimulation(KMart, n, m, False)
    # power = kmart_audit_simulation.power(0.5, alpha=0.065, progression=True)
    # # 0.052
    # print(power)


    n = 500
    m = -1
    # bravo_audit_simulation = AuditSimulation(BRAVO, n, m, False)
    # power = bravo_audit_simulation.power(0.50, p=0.55, alpha=0.18)
    # # 0.0502
    # print(power)
    # power = bravo_audit_simulation.power(0.50, p=0.7, alpha=0.07)
    # # 0.053
    # print(power)
    #
    # bayesian_audit_simulation = AuditSimulation(Bayesian, n, m, False)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=1, thresh=0.99776)
    # # 0.0507
    # print(power)
    # power = bayesian_audit_simulation.power(0.50, a=4, b=1, thresh=0.999075)
    # # 0.0507
    # print(power)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=4, thresh=0.99555)
    # # 0.0507
    # print(power)

    # bayesian_audit_simulation = AuditSimulation(HyperGeomBayesian, n, m, False)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=1, thresh=0.99776, progression=True)
    #
    # print(power)

    # clip_audit_simulation = AuditSimulation(Clip, n, m, False)
    # power = clip_audit_simulation.power(0.5, n=n, alpha=0.075)
    # # 0.0504
    # print(power)
    #
    # kmart_audit_simulation = AuditSimulation(KMart, n, m, False)
    # power = kmart_audit_simulation.power(0.5, alpha=0.05, progression=True)
    # print(power)

    # n = 5000
    # m = 50
    # bravo_audit_simulation = AuditSimulation(HyperGeomBRAVO, n, m, False)
    # power = bravo_audit_simulation.power(0.50, p=0.55, alpha=0.25)
    # # 0.052
    # print(power)
    # power = bravo_audit_simulation.power(0.50, p=0.7, alpha=0.072)
    # # 0.052
    # print(power)
    #
    # bayesian_audit_simulation = AuditSimulation(Bayesian, n, m, False)
    # power = bayesian_audit_simulation.power(0.50, a=1, b=1, thresh=0.8)
    # # 0.052
    # print(power)
    #
    # # bayesian_audit_simulation = AuditSimulation(HyperGeomBayesian, n, m, False)
    # # power = bayesian_audit_simulation.power(0.50, a=1, b=1, thresh=0.05, progression=True)
    # # print(power)
    #
    # clip_audit_simulation = AuditSimulation(Clip, n, m, False)
    # power = clip_audit_simulation.power(0.5, n=n, alpha=0.075)
    # # 0.0504
    # print(power)
    #
    kmart_audit_simulation = AuditSimulation(KMart, n, m, False)
    power = kmart_audit_simulation.power(0.5, alpha=0.09, progression=True)
    print(power)