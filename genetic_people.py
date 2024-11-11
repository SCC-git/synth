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
import itertools
from scipy import stats
from constants import tables_and_characteristics_with_nas


def calculate_error(error_people: [[]], eds_aggregates):
    total_error = 0

    everyones_characteristics = [i for i in list(itertools.chain.from_iterable(error_people))]

    counter = Counter(everyones_characteristics)
    for error_characteristic in error_columns:
        total_error += abs(counter[error_characteristic] -
                           eds_aggregates[error_characteristic])

    return total_error


def calculate_correlation(error_people: [[]], eds_proportions: []):
    synthetic_characteristics = [i for i in list(itertools.chain.from_iterable(error_people))]
    synthetic_counter = Counter(synthetic_characteristics)

    synthetic_table_totals = defaultdict(int)
    for characteristic, count in synthetic_counter.items():
        synthetic_table_totals[characteristic[:4]] += count

    synthetic_population_size = max(synthetic_table_totals.values())

    our_proportions = []
    # This for loop is performed in the same order as for the SAPS marginals
    for table, characteristics in tables_and_characteristics.items():
        # This for loop is performed in the same order as for the SAPS marginals
        tables_proportions = []
        for characteristic in characteristics:
            if characteristic != "":
                tables_proportions.append(
                    synthetic_counter[characteristic] / synthetic_population_size)
            else:
                tables_proportions.append(
                    (synthetic_population_size - synthetic_table_totals[table]) / synthetic_population_size)
        our_proportions.extend(tables_proportions)

    return stats.pearsonr(our_proportions, eds_proportions)


# Here mutate means swap for a different possible person
def mutate(individual, mutation_rate, all_adults: [[]], all_children: [[]]):
    childrens_ages = ["T1_1AGE0_4M",
                      "T1_1AGE5_9M",
                      "T1_1AGE10_14M",
                      "T1_1AGE0_4F",
                      "T1_1AGE5_9F",
                      "T1_1AGE10_14F"]

    people_to_mutate = [i for i in range(len(individual)) if random.uniform(0, 1) < mutation_rate]
    # new_people = random.sample(people, len(people_to_mutate))
    # new_people = [random.sample(adults)]
    for counter, persons_idx in enumerate(people_to_mutate):
        if any(childrens_age in individual[persons_idx] for childrens_age in childrens_ages):
            individual[persons_idx] = random.sample(all_children, 1)[0]
        else:
            individual[persons_idx] = random.sample(all_adults, 1)[0]
    return individual


# Swapping people here rather than households
def crossover(parent_one, parent_two, uniform_rate):
    indexes_to_crossover = [i for i in range(len(parent_one)) if random.uniform(0, 1) < uniform_rate]

    child1 = parent_one.copy()
    child2 = parent_two.copy()

    for i in indexes_to_crossover:
        child1[i] = parent_two[i]
        child2[i] = parent_one[i]

    return [child1, child2]


def tournament_selection(full_population: [[[]]], fitnesses, tournament_size):
    # Machine learning mastery way
    # first random selection
    best_idx = np.random.randint(len(full_population))
    for pop_idx in np.random.randint(0, len(full_population), tournament_size-1):
        # check if better
        # if fitnesses[pop_idx] < fitnesses[best_idx]:
        if fitnesses[pop_idx] > fitnesses[best_idx]:
            best_idx = pop_idx

    return full_population[best_idx]


# def genetic_algorithm(people: [[]], ed_aggregates: pd.DataFrame, population_size: int=50):
def genetic_algorithm(all_adults: [[]], all_children: [[]], ed_aggregates: pd.DataFrame, population_size: int=50):
    # eds = ["167065"] # Navan Rural
    eds = ["68003"] # Barna
    # eds = ["68013"] # Newcastle
    # eds = ed_aggregates["ED_ID"].unique()

    column_to_normalise_off = "T5_2_TP"  # Usually resident people in private households

    table_prefixes = ["T1_1", "T1_2", "T8_1", "T10_"]
    # table_prefixes = ["T1_1", "T1_2", "T5_2", "T8_1", "T10_"]

    # All of these are measured from the present population (T1_1AGETT)
    tables_totals = ["T1_1AGETT", "T1_2T", "T8_1_TT", "T10_4_TT"]  # Don't think we need to rescale T5_2
    # tables_totals = ["T1_1AGETT", "T1_2T", "T5_2_TP", "T8_1_TT", "T10_4_TT"]
    # tables_reference = ["T1_1AGETT", "T1_1AGETT", "T5_2_TP", "T1_1AGETT", "T1_1AGETT"]

    uniform_rate = 0.8
    mutation_rate = 0.1
    tournament_size = 10
    # elitism = True

    childrens_ages = ["T1_1AGE0_4M",
                      "T1_1AGE5_9M",
                      "T1_1AGE10_14M",
                      "T1_1AGE0_4F",
                      "T1_1AGE5_9F",
                      "T1_1AGE10_14F"]

    num_generations = 100

    for ed in eds[:1]:
        this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')[0]

        population_to_normalise_to = this_eds_aggregates[column_to_normalise_off]
        present = this_eds_aggregates["T1_1AGETT"]
        for tot in tables_totals:
            this_eds_aggregates[tot] = round(this_eds_aggregates[tot] * (population_to_normalise_to / present))
        # rescaled_totals = [round(tot * (usually_residents / present)) for tot in tables_totals]

        for i, prefix in enumerate(table_prefixes):
            # Based off Bresenham's line drawing algorithm
            # https://stackoverflow.com/a/31121856s
            columns_with_prefix = {k: v for k, v in this_eds_aggregates.items()
                                   if (prefix in k) and (k in error_columns)}
            unnormalised_sum = sum(columns_with_prefix.values())
            rem = 0
            for characteristic, total in columns_with_prefix.items():
                count = total * this_eds_aggregates[tables_totals[i]] + rem
                this_eds_aggregates[characteristic] = count // unnormalised_sum
                rem = count % unnormalised_sum
            this_eds_aggregates[random.sample(columns_with_prefix.keys(), 1)[0]] += rem

            # print(sum([this_eds_aggregates[k] for k in columns_with_prefix.keys()]))

        # ------------------------- NEW ------------------------------ #
        all_tables_totals_headers = ["T1_1AGETT", "T1_2T", "T5_2_TP", "T8_1_TT", "T10_4_TT"]
        all_tables_totals = {}
        for total in all_tables_totals_headers:
            all_tables_totals[total] = this_eds_aggregates[total]

        their_proportions = []
        for table, characteristics in tables_and_characteristics.items():
            # Get total value of table
            for total_header, total_value in all_tables_totals.items():
                if table in total_header:
                    tables_total = total_value
                    break

            ordered_saps_marginals = []
            for characteristic in characteristics:
                if characteristic != "":
                    ordered_saps_marginals.append(this_eds_aggregates[characteristic] / population_to_normalise_to)
                else:
                    ordered_saps_marginals.append((population_to_normalise_to - tables_total) / population_to_normalise_to)

            their_proportions.extend(ordered_saps_marginals)

        n_children = 0
        for childrens_age in childrens_ages:
            n_children += this_eds_aggregates[childrens_age]

        # TODO: Is this right?
        n_adults = this_eds_aggregates["T5_2_TP"] - n_children
        # size_of_ed = - np.inf
        # for characteristic, aggregate in this_eds_aggregates.items():
        #     if isinstance(aggregate, int) and (characteristic != "ED_ID") and (aggregate > size_of_ed):
        #         size_of_ed = aggregate

        # Initialise population with random individuals (lists of people)
        population = []
        for idx in range(population_size):
            pops_adults = random.choices(all_adults, k=n_adults)
            pops_children = random.choices(all_children, k=n_children)
            population.append(pops_adults + pops_children)
            # population.append(random.choices(people, size_of_ed))

        # best, best_eval = 0, calculate_error(population[0], this_eds_aggregates)
        best, best_eval = 0, calculate_correlation(population[0], their_proportions)

        for generation in range(num_generations):
            # fitnesses = [calculate_error(pop, this_eds_aggregates) for pop in population]
            fitnesses = [calculate_correlation(pop, their_proportions) for pop in population]
            for i in range(population_size):
                # if fitnesses[i] < best_eval:
                if fitnesses[i] > best_eval:
                    best, best_eval = population[i], fitnesses[i]
                    print(f">{generation}, new best = {fitnesses[i]}")

            new_population = []
            parents = [tournament_selection(population, fitnesses, tournament_size) for _ in range(population_size)]

            for i in tqdm(range(0, population_size, 2)):
            # for i in range(0, population_size, 2):
                p1 = parents[i]
                p2 = parents[i+1]

                new_individuals = crossover(p1, p2, uniform_rate)

                for new_individual in new_individuals:
                    # Mutate
                    new_population.append(mutate(new_individual, mutation_rate, all_adults, all_children))

            population = new_population

        print(f"\nED: {ed}")

        our_error_characteristic_counts = defaultdict(int)
        for fittest_person in best:
            for characteristic in fittest_person:
                our_error_characteristic_counts[characteristic] += 1

        # Print population
        for idx, individual in enumerate(best):
            print(f"Person {idx}: {individual}")

        print("\nCharacteristic counts: Ours | Theirs")
        topic_counts = {}
        eds_aggregates_by_topic = {}
        for ed_characteristic, ed_count in this_eds_aggregates.items():
            if ed_characteristic in error_columns:
                print(f"{ed_characteristic}: \t\t\t\t{our_error_characteristic_counts[ed_characteristic]} | {ed_count}")

                if ed_characteristic[:4] in topic_counts:
                    topic_counts[ed_characteristic[:4]] += our_error_characteristic_counts[ed_characteristic]
                else:
                    topic_counts[ed_characteristic[:4]] = our_error_characteristic_counts[ed_characteristic]

                if ed_characteristic[:4] in eds_aggregates_by_topic:
                    eds_aggregates_by_topic[ed_characteristic[:4]] += ed_count
                else:
                    eds_aggregates_by_topic[ed_characteristic[:4]] = ed_count

        print("\nTopics")
        print("Characteristic: Ours | Theirs")
        for topic, topic_count in topic_counts.items():
            print(f"{topic}: {topic_count} | {eds_aggregates_by_topic[topic]}")


if __name__ == '__main__':
    ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
    new_employment_name_male = "T8_1_UNEM"
    new_employment_name_female = "T8_1_UNEF"
    detailed_unemployments_male = ["T8_1_LFFJM", "T8_1_STUM", "T8_1_LTUM"]
    detailed_unemployments_female = ["T8_1_LFFJF", "T8_1_STUF", "T8_1_LTUF"]
    ed_totals[new_employment_name_male] = ed_totals[detailed_unemployments_male].sum(axis=1)
    ed_totals = ed_totals.drop(detailed_unemployments_male, axis=1)
    ed_totals[new_employment_name_female] = ed_totals[detailed_unemployments_female].sum(axis=1)
    ed_totals = ed_totals.drop(detailed_unemployments_female, axis=1)

    # with open("all_predicates.pkl", "rb") as f:
    #     all_people = pkl.load(f)
    # with open("adult_predicates.pkl", "rb") as f:
    #     adults = pkl.load(f)
    # with open("children_predicates.pkl", "rb") as f:
    #     children = pkl.load(f)
    with open("adult_predicates_house_size.pkl", "rb") as f:
        adults = pkl.load(f)
    with open("children_predicates_house_size.pkl", "rb") as f:
        children = pkl.load(f)

    error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
                  r"(^T5_2_)[^T].*P$|" \
                  r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$"

    regex_match_string = re.compile(error_regex)
    error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))
    #
    # lp = LineProfiler()
    # lp.add_function(crossover)
    # lp.add_function(mutate)
    # lp_wrapper = lp(genetic_algorithm)
    # lp_wrapper(q3_households, ed_totals, 50)
    # lp.print_stats()
    # genetic_algorithm(people=all_people, ed_aggregates=ed_totals, population_size=50)
    genetic_algorithm(all_adults=adults, all_children=children, ed_aggregates=ed_totals, population_size=200)
