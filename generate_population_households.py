import math
import random
from collections import defaultdict, Counter
from tqdm import tqdm
import numpy as np
import pandas as pd
import pickle as pkl
import re
from lfs_status_converters import household_size, employment_status, highest_level_of_education
from constants import tables_and_characteristics_with_nas, saps_ages, sexes, saps_marital_statuses
from utils import dupe_dict
import argparse


def calculate_error(error_households: [{dict}], eds_aggregates):
    total_error = 0
    our_error_characteristic_counts = defaultdict(int)
    for error_household in error_households:
        for _, error_individual in error_household.items():
            for error_characteristic in error_individual:
                our_error_characteristic_counts[error_characteristic] += 1

    for error_characteristic in error_columns:
        total_error += abs(our_error_characteristic_counts[error_characteristic] -
                           eds_aggregates[error_characteristic])

    return total_error


def mutate(individual, mutation_rate, households):
    households_to_mutate = [i for i in range(len(individual)) if random.uniform(0, 1) < mutation_rate]
    new_household_keys = random.sample(list(households.keys()), len(households_to_mutate))
    for counter, household_idx in enumerate(households_to_mutate):
        new_household = households[new_household_keys[counter]]

        individual[household_idx] = new_household

    return individual


def crossover(parent_one, parent_two, uniform_rate):
    indexes_to_crossover = [i for i in range(len(parent_one)) if random.uniform(0, 1) < uniform_rate]

    child1 = parent_one.copy()
    child2 = parent_two.copy()

    for i in indexes_to_crossover:
        child1[i] = parent_two[i]
        child2[i] = parent_one[i]

    return [child1, child2]


def tournament_selection(full_population, fitnesses, tournament_size):
    # Machine learning mastery way
    # first random selection
    best_idx = np.random.randint(len(full_population))
    for pop_idx in np.random.randint(0, len(full_population), tournament_size-1):
        # check if better
        if fitnesses[pop_idx] < fitnesses[best_idx]:
            best_idx = pop_idx

    return full_population[best_idx]


def genetic_algorithm(households: {str: {str: []}}, ed_aggregates: pd.DataFrame, population_size: int=50):
    results_folder = "./results/ga/"

    eds = ed_aggregates["ED_ID"].unique()

    uniform_rate = 0.7
    mutation_rate = 0.05
    tournament_size = 10
    # elitism = True

    old_ed_totals = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")
    old_ed_totals["ED_ID"] = old_ed_totals["ED_ID"].astype(str)

    num_generations = 250

    for ed in tqdm(eds):
        this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')
        if len(this_eds_aggregates) > 1:
            temp = {}
            for key, value in this_eds_aggregates[0].items():
                if key not in ["GUID", "GEOGID", "GEOGDESC", "ED_ID"]:
                    temp[key] = sum([ed_with_this_id_aggregates[key] for ed_with_this_id_aggregates in this_eds_aggregates])
                else:
                    temp[key] = value
            this_eds_aggregates = temp
        else:
            this_eds_aggregates = this_eds_aggregates[0]

        num_households_in_ed = sum(old_ed_totals.loc[old_ed_totals["ED_ID"]==str(ed), "T6_3_TH"])
        if num_households_in_ed > len(households):
            households = dupe_dict(households, num_households_in_ed)

        # Initialise population with random individuals (lists of households)
        population = []
        for idx in range(population_size):
            random_household_keys = random.sample(list(households.keys()), num_households_in_ed)
            population.append([households[key] for key in random_household_keys])

        best, best_eval = 0, calculate_error(population[0], this_eds_aggregates)

        for generation in tqdm(range(num_generations)):
            # print(f"Generation: {generation}\n")
            fitnesses = [calculate_error(pop, this_eds_aggregates) for pop in population]
            for i in range(population_size):
                if fitnesses[i] < best_eval:
                    best, best_eval = population[i], fitnesses[i]

            new_population = []
            parents = [tournament_selection(population, fitnesses, tournament_size) for _ in range(population_size)]

            for i in range(0, population_size, 2):
                p1 = parents[i]
                p2 = parents[i+1]

                children = crossover(p1, p2, uniform_rate)

                for child in children:
                    # Mutate
                    new_population.append(mutate(child, mutation_rate, households))

            population = new_population

        if "/" in ed:
            ed = ed.replace("/", "_")
        with open(results_folder + f"{ed}.pkl", "wb") as f:
            pkl.dump(best, f)


def simulated_annealing(households: {str: {str: {}}}, ed_aggregates: pd.DataFrame):
    results_folder = "./results/simulated_annealing/"

    old_ed_totals = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")
    old_ed_totals["ED_ID"] = old_ed_totals["ED_ID"].astype(str)

    eds = ed_aggregates["ED_ID"].unique()
    for ed in tqdm(eds):
        this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')
        if len(this_eds_aggregates) > 1:
            temp = {}
            for key, value in this_eds_aggregates[0].items():
                if key not in ["GUID", "GEOGID", "GEOGDESC", "ED_ID"]:
                    temp[key] = sum([ed_with_this_id_aggregates[key] for ed_with_this_id_aggregates in this_eds_aggregates])
                else:
                    temp[key] = value
            this_eds_aggregates = temp
        else:
            this_eds_aggregates = this_eds_aggregates[0]

        num_households_in_ed = sum(old_ed_totals.loc[old_ed_totals["ED_ID"]==str(ed), "T6_3_TH"])
        if num_households_in_ed > len(households):
            households = dupe_dict(households, num_households_in_ed)

        control_parameter = num_households_in_ed // 2
        random_household_keys = random.sample(households.keys(), num_households_in_ed)
        potential_households = [households[key] for key in random_household_keys]

        old_error, our_final_totals = calculate_error(potential_households, this_eds_aggregates)
        error_stopping_criteria = num_households_in_ed
        best_solution = None
        best_error = np.inf
        num_repeats_at_temp_1 = 0
        while True:
            if control_parameter < 1:
                control_parameter = 1
                num_repeats_at_temp_1 += 1
            num_iterations = int(1_000 // (0.1 * control_parameter))
            for _ in tqdm(range(num_iterations)):
                to_remove = random.sample(potential_households, control_parameter)
                to_add_keys = random.sample(households.keys(), control_parameter)
                to_add_values = [households[key] for key in to_add_keys]

                possible_new_households = []

                already_removed = []
                for old in potential_households:
                    if (old in to_remove) and (old not in already_removed):
                        already_removed.append(old)
                        possible_new_households.append(to_add_values.pop())
                    else:
                        possible_new_households.append(old)

                new_error, possible_final_totals = calculate_error(possible_new_households, this_eds_aggregates)
                change_in_error = new_error - old_error

                if (change_in_error <= 0) or (math.exp(- change_in_error / control_parameter) > random.random()): # Improvement
                    # Accept changes
                    potential_households[:] = possible_new_households
                    old_error = new_error

                    # See if global best
                    if new_error < best_error:
                        best_solution = possible_new_households
                        best_error = old_error
                        our_final_totals = possible_final_totals

            # Update temperature
            control_parameter = math.floor(0.85 * control_parameter)

            print(f"Best Error: {best_error}")
            if (best_error <= error_stopping_criteria) or (num_repeats_at_temp_1 > 20):
                break

        if "/" in ed:
            ed = ed.replace("/", "_")
        with open(results_folder + f"{ed}.pkl", "wb") as f:
            pkl.dump(best_solution, f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("approach", default="genetic_algorithm", choices=["genetic_algorithm", "simulated_annealing"])
    args = parser.parse_args()
    approach = args.approach

    folder = "0061-00 LFS_Q11998-Q32023/0061-00 LFS/0061-00_Data/CSV/"
    file = "0061-24_lfs_2023.csv"

    micro_df = pd.read_csv(folder + file)
    micro_df = micro_df[micro_df["refperiod"] == "2023Q3"]

    household_size_counts = Counter(micro_df["QHHNUM"].tolist())

    micro_df["T1_1"] = micro_df.apply(lambda row: saps_ages[row["AGECLASS"]] + sexes[row["SEX"]], axis=1)
    micro_df["T1_2"] = micro_df.apply(lambda row: saps_marital_statuses[row["MARSTAT"]] + sexes[row["SEX"]], axis=1)
    micro_df["T5_2"] = micro_df["QHHNUM"].apply(lambda x: household_size(x, household_size_counts))
    micro_df["T8_1"] = micro_df.apply(employment_status, axis=1)
    micro_df["T10_"] = micro_df.apply(highest_level_of_education, axis=1)
    grouped = micro_df.groupby(["QHHNUM"])
    q3_households = {}
    for household, group in grouped:
        q3_households[household] = {}
        for idx, individual in group.iterrows():
            q3_households[household][idx] = []
            q3_households[household][idx].append(individual["T1_1"])
            q3_households[household][idx].append(individual["T1_2"])
            q3_households[household][idx].append(individual["T5_2"])
            q3_households[household][idx].append(individual["T8_1"])
            q3_households[household][idx].append(individual["T10_"])

    ed_totals = pd.read_csv("rescaled_ed_aggregates_ordered.csv")

    error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T1_2).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T5_2_)[^T].*P$|" \
                  r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$"
    regex_match_string = re.compile(error_regex)
    error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

    if approach == "genetic_algorithm":
        genetic_algorithm(households=q3_households, ed_aggregates=ed_totals, population_size=100)
    elif approach == "simulated_annealing":
        simulated_annealing(households=q3_households, ed_aggregates=ed_totals)
