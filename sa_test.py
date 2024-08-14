import cProfile
import math
import pstats
from pstats import SortKey
import random
import sys
from collections import defaultdict
import numpy as np
import pickle as pkl
import pandas as pd
from tqdm import tqdm
import re


def simulated_annealing(households: [int]):
    size_of_ed = 200
    control_parameter = size_of_ed // 2
    initial_households = random.sample(households, size_of_ed)

    def calculate_error(error_households: [int]):
        return sum(error_households)

    old_error = calculate_error(initial_households)
    error_stopping_criteria = (sorted(households)[0] * size_of_ed) * 2
    best_solution = None
    best_error = np.inf
    while True:
        if control_parameter < 1:
            control_parameter = 1
        num_iterations = int(1_000 // (0.1 * control_parameter))
        for _ in tqdm(range(num_iterations)):
            to_remove = random.sample(initial_households, control_parameter)
            to_add = random.sample(households, control_parameter)

            possible_new_households = []
            already_removed = []
            for old in initial_households:
                if (old in to_remove) and (old not in already_removed):
                    already_removed.append(old)
                    possible_new_households.append(to_add.pop())
                else:
                    possible_new_households.append(old)

            new_error = calculate_error(possible_new_households)
            change_in_error = new_error - old_error

            if (change_in_error <= 0) or (math.exp(- change_in_error / control_parameter) > random.random()): # Improvement
                # Accept changes
                initial_households[:] = possible_new_households
                old_error = new_error

                # See if global best
                if new_error < best_error:
                    best_solution = possible_new_households
                    best_error = old_error

        # Update temperature
        control_parameter = math.floor(0.85 * control_parameter)

        print(f"Temperature: {control_parameter}")
        print(f"Best Error: {best_error}")

        # if (control_parameter < min_temperature) or (best_error < error_stopping_criteria):
        if best_error < error_stopping_criteria:
            break

    print(f"Final error: {best_error}")
    print(f"Sum of first {size_of_ed}: {sum(sorted(households)[:size_of_ed])}")
    print(f"Best possible (smallest element repeated): {error_stopping_criteria / 2}")

    # for characteristic, count in our_final_totals.items():
    #     print(f"\t{characteristic}: {count} | {this_eds_aggregates[characteristic]}")
    print(f"Final population: {best_solution}\n")


if __name__ == '__main__':
    input_numbers = np.random.randint(1, 10000, 1000).tolist()

    simulated_annealing(households=input_numbers)


