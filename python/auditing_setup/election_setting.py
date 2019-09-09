class Election:
    """
    Stores the current election information and is used to feed to the audit_method for initialisation of auditing.
    """
    def __init__(self, n, m, step=1, replacement=False, p=1/2):
        self.n = n
        self.m = m
        self.step = step
        self.replacement = replacement
        self.p = p
