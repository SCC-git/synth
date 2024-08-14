# import cProfile
import math
# import pstats
import random
# import sys
from collections import defaultdict
import numpy as np
import pickle as pkl
import pandas as pd
from tqdm import tqdm
import re
# from pstats import SortKey
# import line_profiler
import os

# os.environ["LINE_PROFILE"] = "1"

# column_strings_to_match = [
#     # NOT INCLUDING TOTALS FOR ANY OF THESE
#     r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$",  # Age and Sex (18+)
#     r"(^T1_2).+(?<!T)(?<!TM)(?<!TF)$",  # Marital Status
#     # r"(^T2_1)[^T].*C$",  # Citizenship
#     r"(^T2_2)[^T].*",  # Ethnicity
#     # r"(^T2_4)[^T].*",  # Religion
#     # r"(^T3_1)[^T].*",  # Irish speaking ability
#     r"(^T5_1)[^T].*P$",  # Household Type (persons only for now) TODO: Include households?
#     # r"(^T5_2_)[^T].*P$",  # Household Size (persons only for now)
#     r"(^T6_3_)[^T].*P$",  # Household Type of Occupancy (persons only for now)
#     r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$",  # Principal Economic Status
#     # r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$",  # Highest Level of Education Completed (15 or over)
#     # r"(^T12_1_)[^T]"  # Disability by sex
#     # r"(^T12_3).+(?<!T)(?<!TM)(?<!TF)$"  # General Health by sex
# ]


# class Individual:
#     pass


def simulated_annealing(households: {str: {str: {}}}, ed_aggregates: pd.DataFrame, error_columns: []):


    # eds = ed_aggregates["ED_ID"].unique()
    # print(len(eds))
    # for ed in eds:
    #     print(ed)
    # eds = ["68013"] # Newcastle
    # eds = [267028] # Blanchardstown-Blakestown
    eds = ["167065"] # Navan Rural
    # eds = ["27059"] # Blanchardstown-Blakestown
    for ed in eds[:1]:
        this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')[0]

        size_of_ed = this_eds_aggregates["T6_3_TH"]
        control_parameter = size_of_ed // 2
        random_household_keys = random.sample(households.keys(), size_of_ed)
        potential_households = [households[key] for key in random_household_keys]

        def calculate_error(error_households: [{dict}]):
            total_error = 0

            our_error_characteristic_counts = defaultdict(int)
            for error_household in error_households:
                for _, error_individual in error_household.items():
                    for table, value in error_individual.items():
                        # Value is not blank in SAPS data
                        if (table != "others") and ("T" in value):
                            our_error_characteristic_counts[value] += 1
                    # for error_characteristic in error_columns:
                    #     # try:
                    #     #     our_count = int(individual[error_characteristic])
                    #     #     our_error_characteristic_counts[error_characteristic] += our_count
                    #     # except:
                    #     #     continue
                    #     if error_characteristic in individual:
                    #         our_error_characteristic_counts[error_characteristic] += 1

            for error_characteristic in error_columns:
                total_error += abs(our_error_characteristic_counts[error_characteristic] -
                                   this_eds_aggregates[error_characteristic])

            return total_error, our_error_characteristic_counts

        old_error, our_final_totals = calculate_error(potential_households)
        min_temperature = 5
        # error_stopping_criteria = 10
        # error_stopping_criteria = size_of_ed * 0.05
        error_stopping_criteria = 7000
        # error_stopping_criteria = 15
        print(f"error_stopping_criteria: {error_stopping_criteria}")
        best_solution = None
        best_error = np.inf
        while True:
            if control_parameter < 1:
                control_parameter = 1
            num_iterations = int(1_000 // (0.1 * control_parameter))
            # num_iterations = int(5_000 // (0.1 * control_parameter))
            for _ in tqdm(range(num_iterations)):
                # print(f"len(potential_households): {len(potential_households)}")
                # print(f"control_parameter: {control_parameter}\n")
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

                new_error, possible_final_totals = calculate_error(possible_new_households)
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

                # else:
                # Don't change old_error
                # Don't update potential households
            # Update temperature
            control_parameter = math.floor(0.85 * control_parameter)

            print(f"Temperature: {control_parameter}")
            print(f"Best Error: {best_error}")
            # break
            # if (control_parameter < min_temperature) or (best_error < error_stopping_criteria):
            if best_error <= error_stopping_criteria:
                break

        print(f"\nED: {ed}")
        print(f"Final error: {best_error}")
        print("Characteristic counts: Ours | Theirs")
        for characteristic, count in our_final_totals.items():
            print(f"\t{characteristic}: {count} | {this_eds_aggregates[characteristic]}")

        print("\nHouseholds:")
        for idx, household in enumerate(best_solution):
            print(f"Household {idx}")
            for individuals_id, individual in household.items():
                print(f"\tIndividual {individuals_id}")
                for error_column in individual.keys():
                    if error_column != "others":
                        print(f"\t\t{individual[error_column]}")
            print("\n")


def quota_sampling(households: {str: {str: {}}}, ed_aggregates: pd.DataFrame, error_columns: []):

    childrens_ages = ["T1_1AGE0_4M",
                      "T1_1AGE5_9M",
                      "T1_1AGE10_14M",
                      "T1_1AGE0_4F",
                      "T1_1AGE5_9F",
                      "T1_1AGE10_14F"]

    # eds = ed_aggregates["ED_ID"].unique()
    eds = ["68013"] # Newcastle
    # eds = ["167065"] # Navan Rural
    for ed in eds[:1]:
        # Create quotas
        this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')[0]
        quota_totals = {k: v for k, v in this_eds_aggregates.items() if k in error_columns}

        # Key: household_id, Value: dictionary of characteristic totals
        candidate_households_values = {}

        print("\nPre-Screening:")
        print("\tRemoving households which are above a quota from the beginning")
        # Remove unsuitable households
        for household_id, individuals in households.items():
            household_characteristic_counts = defaultdict(int)
            household_valid_thus_far = True
            for individuals_id, individual in individuals.items():
                for table_header, individuals_value in individual.items():
                    if (table_header != "others") and ("T" in individuals_value):
                        household_characteristic_counts[individuals_value] += 1
                        if household_characteristic_counts[individuals_value] > quota_totals[individuals_value]:
                            print(f"Household {household_id} unsuitable: {individuals_value} exceeded")
                            print(f"Household value: {household_characteristic_counts[individuals_value]}")
                            print(f"Aggregate value: {quota_totals[individuals_value]}")
                            household_valid_thus_far = False
                            break

                if not household_valid_thus_far:
                    break

            # Household valid through all individuals
            if household_valid_thus_far:
                candidate_households_values[household_id] = household_characteristic_counts

        admitted_households = {}

        print("\nProgressive Iteration")
        print("\tAdding households according to the running quota totals")
        consecutive_non_adds = 0
        consecutive_non_add_threshold = 500
        houses_tried = 0

        children_households = {}
        configuration = 0
        # for household_id, household_characteristic_dict in candidate_households_values.items():
        #     if any(v in childrens_ages for v in household_characteristic_dict):
        #         children_households[household_id] = household_characteristic_dict
        # populations_to_sample = [children_households, ]
        while (any(value > 0 for value in quota_totals.values())) and candidate_households_values:
            houses_tried += 1
            print(f"Houses Tried: {houses_tried} | Consecutive non-adds: {consecutive_non_adds}")

            # if configuration > 1:
            # print(configuration)
            # population_to_sample = populations_to_sample[configuration]

            household_id = random.sample(candidate_households_values.keys(), 1)[0]
            household_characteristic_dict = candidate_households_values[household_id]
            # household_id = random.sample(population_to_sample.keys(), 1)[0]
            # household_characteristic_dict = population_to_sample[household_id]
            # index_of_household = random.randint(0, len(candidate_households_as_list)-1)
            # household, household_characteristic_dict = candidate_households_as_list[index_of_household]
            # for household, household_characteristic_dict in candidate_households_as_list:
            household_valid_thus_far = True
            for characteristic, household_count in household_characteristic_dict.items():
                if household_count > quota_totals[characteristic]:
                    household_valid_thus_far = False
                    break

            if household_valid_thus_far:
                print(f"ADDING HOUSE {household_id}")
                consecutive_non_adds = 0

                # Reduce quota by amount in household
                for characteristic, household_count in household_characteristic_dict.items():
                    quota_totals[characteristic] -= household_count

                    # Quota full, remove all households with those people
                    if quota_totals[characteristic] < 1:
                        print(f"{characteristic} done")
                        print(f"\tRemoving all households with a {characteristic} in it")
                        candidate_households_values = {k: v for k, v in candidate_households_values.items()
                                                       if characteristic not in v}

                        # population_to_sample = {k: v for k, v in population_to_sample.items()
                        #                                if characteristic not in v}
                        # for candidate_household_id, candidate_household_values in candidate_households_values.items():
                        #     if characteristic in candidate_household_values:
                        #         to_remove.append(can)

                # Add to final list of households
                admitted_households[household_id] = household_characteristic_dict
                # Remove from candidate list
                candidate_households_values.pop(household_id, None)
                # population_to_sample.pop(household_id, None)
                # candidate_households_as_list.pop(index_of_household)
            else:
                consecutive_non_adds += 1

            # if (consecutive_non_adds >= consecutive_non_add_threshold) or (not population_to_sample):
            #     configuration += 1
            #     if configuration < len(populations_to_sample):
            #         consecutive_non_adds = 0
            #         print("\n\n------------------------------ CHANGING CONFIGURATION ----------------------------\n\n")
            #     else:
            #         break

        for characteristic, count in quota_totals.items():
            print(f"{characteristic}: {count} left to fill")


def quota_sampling_configs(households: {str: {str: {}}}, ed_aggregates: pd.DataFrame, error_columns: []):
    # error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$"
    # regex_match_string = re.compile(error_regex)
    # error_columns = sorted(list(filter(regex_match_string.match, ed_aggregates.columns)))

    childrens_ages = ["T1_1AGE0_4M",
                      "T1_1AGE5_9M",
                      "T1_1AGE10_14M",
                      "T1_1AGE0_4F",
                      "T1_1AGE5_9F",
                      "T1_1AGE10_14F"]

    # eds = ed_aggregates["ED_ID"].unique()
    # eds = ["68013"] # Newcastle
    eds = ["167065"] # Navan Rural
    for ed in eds[:1]:
        # Create quotas
        this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')[0]
        quota_totals = {k: v for k, v in this_eds_aggregates.items() if k in error_columns}

        # Key: household_id, Value: dictionary of characteristic totals
        candidate_households_values = {}

        print("\nPre-Screening:")
        print("\tRemoving households which are above a quota from the beginning")
        # Remove unsuitable households
        for household_id, individuals in households.items():
            household_characteristic_counts = defaultdict(int)
            household_valid_thus_far = True
            for individuals_id, individual in individuals.items():
                for table_header, individuals_value in individual.items():
                    if (table_header != "others") and ("T" in individuals_value):
                        household_characteristic_counts[individuals_value] += 1
                        if household_characteristic_counts[individuals_value] > quota_totals[individuals_value]:
                            print(f"Household {household_id} unsuitable: {individuals_value} exceeded")
                            print(f"Household value: {household_characteristic_counts[individuals_value]}")
                            print(f"Aggregate value: {quota_totals[individuals_value]}")
                            household_valid_thus_far = False
                            break

                if not household_valid_thus_far:
                    break

            # Household valid through all individuals
            if household_valid_thus_far:
                candidate_households_values[household_id] = household_characteristic_counts

        admitted_households = {}

        print("\nProgressive Iteration")
        print("\tAdding households according to the running quota totals")
        consecutive_non_adds = 0
        consecutive_non_add_threshold = 5000
        houses_tried = 0

        # Key = household size, Value = list of households with that size
        households_by_size = defaultdict(dict)

        children_households = {}
        configuration = 0
        for household_id, household_characteristic_dict in candidate_households_values.items():
            if any(v in childrens_ages for v in household_characteristic_dict):
                children_households[household_id] = household_characteristic_dict

            for characteristic, count in household_characteristic_dict.items():
                if "T5_2" in characteristic:
                    households_by_size[count][household_id] = household_characteristic_dict

        # sorted_by_household_size = {k: v for k, v in sorted(candidate_households_values.items(),
        #                                                     key=lambda item: item[1]["T5_2"].strip("PP")[-1])}
        populations_to_sample = [children_households]
        populations_to_sample.extend([households_by_size[size] for size in sorted(households_by_size.keys(), reverse=True)])
        populations_to_sample.append(candidate_households_values)
        # config_2_household_id = 0
        # config_2_current_households_size = max(households_by_size.keys())
        while (any(value > 0 for value in quota_totals.values())) and candidate_households_values:
            houses_tried += 1
            print(f"Houses Tried: {houses_tried} | Consecutive non-adds: {consecutive_non_adds}")

            # if configuration > 1:
            # print(configuration)
            # if configuration not in [0, len(populations_to_sample) - 1]:
            #     if len(population_to_sample.keys()) == 0:
            #         configuration += 1
            population_to_sample = populations_to_sample[configuration]

            # household_id = random.sample(candidate_households_values.keys(), 1)[0]
            # household_characteristic_dict = candidate_households_values[household_id]

            household_id = random.sample(population_to_sample.keys(), 1)[0]
            household_characteristic_dict = population_to_sample[household_id]
            # index_of_household = random.randint(0, len(candidate_households_as_list)-1)
            # household, household_characteristic_dict = candidate_households_as_list[index_of_household]
            # for household, household_characteristic_dict in candidate_households_as_list:
            household_valid_thus_far = True
            for characteristic, household_count in household_characteristic_dict.items():
                if household_count > quota_totals[characteristic]:
                    household_valid_thus_far = False
                    print(f"\t{household_id} not valid")
                    print(f"\t{characteristic}: {household_count} > {quota_totals[characteristic]}")
                    break

            if household_valid_thus_far:
                print(f"ADDING HOUSE {household_id}")
                consecutive_non_adds = 0

                # Reduce quota by amount in household
                for characteristic, household_count in household_characteristic_dict.items():
                    quota_totals[characteristic] -= household_count

                    # Quota full, remove all households with those people
                    if quota_totals[characteristic] < 1:
                        print(f"{characteristic} done")
                        print(f"\tRemoving all households with a {characteristic} in it")
                        candidate_households_values = {k: v for k, v in candidate_households_values.items()
                                                       if characteristic not in v}

                        population_to_sample = {k: v for k, v in population_to_sample.items()
                                                       if characteristic not in v}
                        # for candidate_household_id, candidate_household_values in candidate_households_values.items():
                        #     if characteristic in candidate_household_values:
                        #         to_remove.append(can)

                # Add to final list of households
                admitted_households[household_id] = household_characteristic_dict
                # Remove from candidate list
                candidate_households_values.pop(household_id, None)
                population_to_sample.pop(household_id, None)
                # candidate_households_as_list.pop(index_of_household)
            else:
                if configuration not in [0, len(populations_to_sample) - 1]:
                    population_to_sample.pop(household_id, None)
                consecutive_non_adds += 1

            if (consecutive_non_adds >= consecutive_non_add_threshold) or (not population_to_sample):
                configuration += 1
                if configuration < len(populations_to_sample):
                    consecutive_non_adds = 0
                    print("\n\n------------------------------ CHANGING CONFIGURATION ----------------------------\n\n")
                else:
                    break

        for characteristic, count in quota_totals.items():
            print(f"{characteristic}: {count} left to fill")


if __name__ == '__main__':
    # ed_totals = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")
    ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
    with open('2023q3_households_new_schema_more_constraints.pkl', 'rb') as f:
        q3_households = pkl.load(f)

    print(f"Num. households: {len(q3_households)}")

    error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
                  r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T5_2_)[^T].*P$"
    regex_match_string = re.compile(error_regex)
    error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

    simulated_annealing(households=q3_households, ed_aggregates=ed_totals, error_columns=error_columns)
    # quota_sampling(households=q3_households, ed_aggregates=ed_totals, error_columns=error_columns)
    # quota_sampling_configs(households=q3_households, ed_aggregates=ed_totals, error_columns=error_columns)



