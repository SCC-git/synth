import random
from collections import defaultdict, Counter
from tqdm import tqdm
import numpy as np
import pandas as pd
import pickle as pkl
import re
import math
from line_profiler import LineProfiler
import os

os.environ["LINE_PROFILE"] = "1"


def calculate_error(error_households: [{dict}], eds_aggregates):
    total_error = 0
    # everyones_characteristics = sum([sum(error_household.values(), []) for error_household in error_households], [])
    everyones_characteristics = []
    # our_error_characteristic_counts = defaultdict(int)
    for error_household in error_households:
        # everyones_characteristics.extend(np.concatenate(error_household.values()))
        everyones_characteristics.extend(sum(error_household.values(), []))
        # for _, error_individual in error_household.items():
            # for table, value in error_individual.items():
            #     # Value is not blank in SAPS data
            #     if (table != "others") and ("T" in value):
            #         our_error_characteristic_counts[value] += 1

            # everyones_characteristics.extend(error_individual)
            # for characteristic in error_individual:
            #     # Value is not blank in SAPS data
            #     if (table != "others") and ("T" in value):
            #         our_error_characteristic_counts[value] += 1
            # for error_characteristic in error_columns:
            #     # try:
            #     #     our_count = int(individual[error_characteristic])
            #     #     our_error_characteristic_counts[error_characteristic] += our_count
            #     # except:
            #     #     continue
            #     if error_characteristic in individual:
            #         our_error_characteristic_counts[error_characteristic] += 1

    counter = Counter(everyones_characteristics)
    for error_characteristic in error_columns:
        # total_error += abs(our_error_characteristic_counts[error_characteristic] -
        #                    eds_aggregates[error_characteristic])
        total_error += abs(counter[error_characteristic] -
                           eds_aggregates[error_characteristic])


    return total_error # , our_error_characteristic_counts


# def crossover(parent_one, parent_two):
#     pass

def tournament_selection(full_population, tournament_size, this_eds_aggregates):
    # Allow repetition, as in the OG paper
    # TODO: check if we should allow repetition
    tournament_population = random.choices(full_population, k=tournament_size)
    tournament_fitnesses = [calculate_error(indv, this_eds_aggregates) for indv in tournament_population]
    tournament_index_of_fittest = tournament_fitnesses.index(min(tournament_fitnesses))
    return tournament_population[tournament_index_of_fittest]


def genetic_algorithm(households: {str: {str: []}}, ed_aggregates: pd.DataFrame, error_columns: [], population_size: int=50):
    # eds = ["167065"] # Navan Rural
    eds = ["68003"] # Barna
    # eds = ["68013"] # Newcastle
    # eds = ed_aggregates["ED_ID"].unique()

    uniform_rate = 0.7
    mutation_rate = 0.05
    tournament_size = 10
    elitism = True

    num_generations = 1

    for ed in eds[:1]:
        this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')[0]

        size_of_ed = this_eds_aggregates["T6_3_TH"]



        # Initialise population with random individuals (lists of households)
        population = []
        fitnesses = []
        for idx in range(population_size):
            random_household_keys = random.sample(households.keys(), size_of_ed)
            population.append([households[key] for key in random_household_keys])

            # Evaluate fitness of each individual
            fitnesses.append(calculate_error(population[idx], this_eds_aggregates))
        print(f"Initial best fitness: {min(fitnesses)}")

        for generation in range(num_generations):
            print(f"Generation: {generation}\n")
            new_population = []
            elitism_offset = 0
            if elitism:
                # Get fittest
                index_of_fittest = fitnesses.index(min(fitnesses))

                # Get new population with fittest as parent
                new_population = [population[index_of_fittest]]
                elitism_offset = 1

            for _ in tqdm(range(elitism_offset, population_size, 2)):
                # print("SELECTION\n")
                first_parent = tournament_selection(population, tournament_size, this_eds_aggregates)
                second_parent = tournament_selection(population, tournament_size, this_eds_aggregates)

                # Crossover
                def crossover(parent_one, parent_two):
                    indexes_to_crossover = [i for i in range(size_of_ed) if random.uniform(0, 1) < uniform_rate]
                    # for i in range(size_of_ed):
                    #     if random.uniform(0, 1) < mutation_rate:
                    #         indexes_to_crossover.append(i)

                    # num_households_to_crossover = round(np.random.normal(loc=uniform_rate * size_of_ed, scale=12))
                    # indexes_to_crossover = random.sample(range(0, size_of_ed - 1), num_households_to_crossover)
                    # parent_two_household_indexes_to_swap = random.sample(range(len(parent_two)-1), num_households_to_swap)

                    child_one = [parent_two[i] if (i in indexes_to_crossover) else parent_one[i] for i in range(len(parent_one))]
                    child_two = [parent_one[i] if (i in indexes_to_crossover) else parent_two[i] for i in range(len(parent_one))]

                    return [child_one, child_two]

                # print("CROSSOVER\n")
                new_individuals = crossover(first_parent, second_parent)

                # Mutation
                def mutate(individual):
                    # num_households_to_mutate = round(np.random.normal(loc=mutation_rate * size_of_ed, scale=5.75))
                    indexes_to_mutate = [i for i in range(size_of_ed) if random.uniform(0, 1) < mutation_rate]
                    if len(indexes_to_mutate) > 0:
                        # indexes_to_mutate = random.sample(range(len(individual)), num_households_to_mutate)
                        mutated_individual = []
                        for i in range(len(individual)):
                            if i not in indexes_to_mutate:
                                mutated_individual.append(individual[i])
                            else:
                                # Put in a different household instead of the old one
                                new_household_key = random.sample(households.keys(), 1)[0]
                                new_household = households[new_household_key]
                                mutated_individual.append(new_household)
                    else:
                        mutated_individual = individual
                    return mutated_individual

                for new_individual in new_individuals:
                    # Mutate
                    new_population.append(mutate(new_individual))
                # new_individual = mutate(new_individual)
                # new_population.extend(mutated_new_individuals)

            population = new_population
            new_fitnesses = [calculate_error(individual, this_eds_aggregates) for individual in population]
            fitnesses = new_fitnesses

            print(f"Fittest fitness: {min(new_fitnesses)}\n")

        print(f"\nED: {ed}")

        fittest_population = population[fitnesses.index(min(fitnesses))]

        our_error_characteristic_counts = defaultdict(int)
        for fittest_household in fittest_population:
            for _, fittest_individual in fittest_household.items():
                # for table, value in fittest_individual.items():
                for characteristic in fittest_individual:
                    our_error_characteristic_counts[characteristic] += 1
                    # Value is not blank in SAPS data
                    # if (table != "others") and ("T" in value):
                    #     our_error_characteristic_counts[value] += 1
        print("Characteristic counts: Ours | Theirs")
        for characteristic, count in our_error_characteristic_counts.items():
            if "T" in characteristic:
                print(f"\t{characteristic}: {count} | {this_eds_aggregates[characteristic]}")

        # print("\nHouseholds:")
        # for idx, household in enumerate(best_solution):
        #     print(f"Household {idx}")
        #     for individuals_id, individual in household.items():
        #         print(f"\tIndividual {individuals_id}")
        #         for error_column in individual.keys():
        #             if error_column != "others":
        #                 print(f"\t\t{individual[error_column]}")
        #     print("\n")


if __name__ == '__main__':
    # ed_totals = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")
    ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
    # with open('2023q3_households_new_schema_more_constraints.pkl', 'rb') as f:
    with open('2023q3_households_new_schema_more_constraints_no_excess.pkl', 'rb') as f:
        q3_households = pkl.load(f)

    print(f"Num. households: {len(q3_households)}")

    error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
                  r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T5_2_)[^T].*P$"
    regex_match_string = re.compile(error_regex)
    error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

    lp = LineProfiler()
    lp.add_function(tournament_selection)
    lp.add_function(calculate_error)
    lp_wrapper = lp(genetic_algorithm)
    lp_wrapper(q3_households, ed_totals, error_columns, 50)
    lp.print_stats()
    # genetic_algorithm(households=q3_households, ed_aggregates=ed_totals, error_columns=error_columns, population_size=50)
