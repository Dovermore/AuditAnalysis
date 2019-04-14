from risk_power_parallel import *
import os
from os import path


# Sanity check for the parallel version of risk power computation

n = 500
m = 200

fpath1 = path.join("..", "..", "data", f"{n:06}{m:04}_w")
fpath2 = path.join("..", "..", "data", f"{n:06}{m:04}_wo")

assert path.exists(fpath2) and path.exists(fpath1)

for fname in os.listdir(fpath1):
    fname1 = path.join(fpath1, fname)
    fname2 = path.join(fpath2, fname)

    df1 = pd.read_csv(fname1, index_col=0)
    df_normal = pd.read_csv(fname2, index_col=0)

    mask: pd.DataFrame = df1 != df_normal
    if mask.any(None):
        print(mask)
