import pytest

import sys
from auditing_setup.audit_methods import *
from auditing_setup.election_setting import Election
from auditing_setup.audit_process import *

import logging

console_logger = logging.getLogger("console_logger")
console_logger.setLevel(logging.INFO)

# Test if the outputs of multiprocessing and serial processing are the same
def test_result():
    election = Election(n=500, m=500, replacement=False, step=1, p=0.5)

    bravo = BRAVO(p=0.3, alpha=0.05, p_0=0.5, election=election)

    result_serial = audit_process_simulation_serial(bravo, election)
    result_parallel = audit_process_simulation_parallel(bravo, election)
    print("final result:", result_serial, result_parallel, file=sys.stderr)
    assert result_serial == result_parallel
