import pytest

from auditing_setup.audit_methods import *
from auditing_setup.election_setting import Election
from auditing_setup.audit_process import *

# Test if the outputs of multiprocessing and serial processing are the same
def test_result():
    election = Election(n=500, m=500, replacement=False, step=1, p=0.5)

    bravo = BRAVO()

    result_serial = stochastic_process_simulation_serial()
    result_parallel = stochastic_process_simulation_parallel
