class Election:
    def __init__(self, n, m, step=1, replacement=False, p0=1/2):
        self.n = n
        self.m = m
        self.step = step
        self.replacement = replacement
        self.p0 = p0
