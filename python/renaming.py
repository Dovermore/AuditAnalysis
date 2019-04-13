import os
from os import path
import re

data_dir = path.join("..", "data", "0100000200_normal")

# Match and remove the inner 10 digits
pattern = re.compile("^([a-z]+_[a-z]+1?)\d{10}(\d+)\.csv$")

for file in os.listdir(data_dir):
    match = pattern.match(file)
    if match:
        old_name = path.join(data_dir, file)

        new_name = f"{match.group(1)}{match.group(2)}.csv"

        print(new_name)
        os.rename(old_name, path.join(data_dir, new_name))
