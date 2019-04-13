from os import path
import os
import re

data_path = path.join("..", "data")

n = 20000
m = 500

table_pattern = re.compile(f"^(\w*)_(table|power|type1)"
                           f"{n:06}{n:04}(\d*)\.csv$")
dsample_pattern = re.compile(f"^(\w*)_(dsample){n:06}{n:04}(\d*)\.csv$")

tables = {}
dsamples = {}

audit_types = ["bayesian", "bravo", "clip"]
audit_types = ["bayesian", "bravo", "clip"]


for file in os.listdir(data_path):
    # Get file name
    file: str = file.rsplit("/")[-1]

    # If matched table pattern
    table_match = table_pattern.match(file)
    if table_pattern.match(file) is not None:
        audit_type = table_match.group(1)
        table_type = table_match.group(2)
        parameter_group = table_match.group(3)

        if audit_type

    dsamples_match = dsample_pattern.match(file)
