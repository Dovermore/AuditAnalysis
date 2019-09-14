#!/bin/bash
# 2 nodes, 2 tasks per node = 4 cores
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=6
#SBATCH --time=0-12:00:00
#SBATCH --partition=physical

# Load required modules
module load Python/3.7.3-spartan_gcc-8.1.0

# Launch multiple process python code
echo "Start running script for audit benchmark"

time mpiexec python3 twitter_search_541635.py -i minitwitter.csv -m
