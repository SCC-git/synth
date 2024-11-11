# import cProfile
import math
# import pstats
import random
# import sys
from collections import defaultdict, Counter
from os import listdir

import numpy as np
import pickle as pkl
import pandas as pd
from tqdm import tqdm
import re
from scipy import stats
# from pstats import SortKey
# import line_profiler
import os
from lfs_status_converters import household_size, employment_status, highest_level_of_education


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
from constants import tables_and_characteristics_with_nas, saps_ages, sexes, saps_marital_statuses
from utils import dupe_dict


def simulated_annealing(households: {str: {str: {}}}, ed_aggregates: pd.DataFrame, error_columns: []):
    results_folder = "./results/simulated_annealing/"
    column_to_normalise_off = "T5_2_TP"

    files = [f.split(".")[0] for f in listdir(results_folder)]

    old_ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
    old_ed_totals["ED_ID"] = old_ed_totals["ED_ID"].astype(str)

    # eds = ed_aggregates["ED_ID"].unique()
    # eds = ["68013"] # Newcastle
    eds = ["267028"] # Blanchardstown-Blakestown
    # eds = ["167065"] # Navan Rural
    # eds = ["27059"]
    # for ed in eds[:1]:
    for ed in tqdm(eds):
        # if "/" in ed:
        #     id_for_lookup = ed.replace("/", "_")
        # else:
        #     id_for_lookup = ed
        # if id_for_lookup in files:
        #     continue

        # this_eds_aggregates = ed_aggregates[ed_aggregates["ED_ID"] == str(ed)].to_dict('records')[0]
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

        # table_prefixes_to_normalise = ["T1_1", "T1_2", "T8_1", "T10_"]
        # tables_totals = ["T1_1AGETT", "T1_2T", "T5_2_TP", "T8_1_TT", "T10_4_TT"]  # Don't think we need to rescale T5_2
        # tables_totals_to_normalise = ["T1_1AGETT", "T1_2T", "T8_1_TT", "T10_4_TT"]  # Don't think we need to rescale T5_2

        # population_to_normalise_to = this_eds_aggregates[column_to_normalise_off]
        population_to_normalise_to = sum(old_ed_totals.loc[old_ed_totals["ED_ID"]==str(ed), column_to_normalise_off])
        # present = this_eds_aggregates["T1_1AGETT"]
        # for tot in tables_totals_to_normalise:
        #     this_eds_aggregates[tot] = round(this_eds_aggregates[tot] * (population_to_normalise_to / present))
        # rescaled_totals = [round(tot * (usually_residents / present)) for tot in tables_totals]

        # for i, prefix in enumerate(table_prefixes_to_normalise):
        #     # Based off Bresenham's line drawing algorithm
        #     # https://stackoverflow.com/a/31121856s
        #     columns_with_prefix = {k: v for k, v in this_eds_aggregates.items()
        #                            if (prefix in k) and (k in error_columns)}
        #     unnormalised_sum = sum(columns_with_prefix.values())
        #     rem = 0
        #     for characteristic, total in columns_with_prefix.items():
        #         count = total * this_eds_aggregates[tables_totals_to_normalise[i]] + rem
        #         this_eds_aggregates[characteristic] = count // unnormalised_sum
        #         rem = count % unnormalised_sum
        #     this_eds_aggregates[random.sample(columns_with_prefix.keys(), 1)[0]] += rem

        num_households_in_ed = sum(old_ed_totals.loc[old_ed_totals["ED_ID"]==str(ed), "T6_3_TH"])
        # TODO: Implement duplication of households if the population is greater than the LFS size
        if num_households_in_ed > len(households):
            households = dupe_dict(households, num_households_in_ed)
            # continue
        control_parameter = num_households_in_ed // 2
        random_household_keys = random.sample(households.keys(), num_households_in_ed)
        potential_households = [households[key] for key in random_household_keys]

        # Calculate proportions of population occupied by each characteristic
        # all_tables_totals_headers = ["T1_1AGETT", "T1_2T", "T5_2_TP", "T8_1_TT", "T10_4_TT"]
        # all_tables_totals = {}
        # for total in all_tables_totals_headers:
        #     all_tables_totals[total] = this_eds_aggregates[total]
        their_proportions = []
        for table, characteristics in tables_and_characteristics_with_nas.items():
            # Get total value of table
            # for total_header, total_value in all_tables_totals.items():
            #     if table in total_header:
            #         tables_total = total_value
            #         break

            ordered_saps_marginals = []
            for characteristic in characteristics:
                # if characteristic != "":
                ordered_saps_marginals.append(this_eds_aggregates[characteristic] / population_to_normalise_to)
                # else:
                #     ordered_saps_marginals.append((population_to_normalise_to - tables_total) / population_to_normalise_to)

            their_proportions.extend(ordered_saps_marginals)

        # def calculate_error(error_households: [{dict}]):
        #     our_error_characteristic_counts = defaultdict(int)
        #     for error_household in error_households:
        #         for _, error_individual in error_household.items():
        #             for table, value in error_individual.items():
        #                 # Value is not blank in SAPS data
        #                 if (table != "others") and ("T" in value):
        #                     our_error_characteristic_counts[value] += 1
        #
        #     our_proportions = []
        #     # This for loop is performed in the same order as for the SAPS marginals
        #     for table, characteristics in tables_and_characteristics.items():
        #         # This for loop is performed in the same order as for the SAPS marginals
        #         for characteristic in characteristics:
        #             if characteristic != "":
        #                 our_proportions[table].append(
        #                     our_error_characteristic_counts[characteristic] / synthetic_population_size)
        #                 # synthetic_counter[characteristic] / synthetic_table_totals[characteristic[:4]])
        #             else:
        #                 our_proportions[table].append(
        #                     (synthetic_population_size - synthetic_table_totals[table]) / synthetic_population_size)
        #
        #     print(f"Pearson's R coefficient (proportions): {stats.pearsonr(our_proportions, their_proportions)}")
        #
        #     # for error_characteristic in error_columns:
        #     #     total_error += abs(our_error_characteristic_counts[error_characteristic] -
        #     #                        this_eds_aggregates[error_characteristic])
        #
        #     return total_error, our_error_characteristic_counts

        def calculate_error(error_households: [{dict}]):
            total_error = 0

            our_error_characteristic_counts = defaultdict(int)
            for error_household in error_households:
                for _, error_individual in error_household.items():
                    # for table, value in error_individual.items():
                    for error_characteristic in error_individual:
                        # # Value is not blank in SAPS data
                        # if (table != "others") and ("T" in value):
                        #     our_error_characteristic_counts[value] += 1
                        our_error_characteristic_counts[error_characteristic] += 1

            for error_characteristic in error_columns:
                total_error += abs(our_error_characteristic_counts[error_characteristic] -
                                   this_eds_aggregates[error_characteristic])

            return total_error, our_error_characteristic_counts

        def calculate_correlation(error_households: [{dict}]):
            synthetic_counts = defaultdict(int)
            for error_household in error_households:
                for _, error_individual in error_household.items():
                    for error_characteristic in error_individual:
                        synthetic_counts[error_characteristic] += 1

            synthetic_table_totals = defaultdict(int)
            for characteristic, count in synthetic_counts.items():
                synthetic_table_totals[characteristic[:4]] += count

            synthetic_population_size = max(synthetic_table_totals.values())

            our_proportions = []
            # This for loop is performed in the same order as for the SAPS marginals
            for table, characteristics in tables_and_characteristics.items():
                # This for loop is performed in the same order as for the SAPS marginals
                for characteristic in characteristics:
                    if characteristic != "":
                        our_proportions.append(
                            synthetic_counts[characteristic] / synthetic_population_size)
                    else:
                        our_proportions.append(
                            (synthetic_population_size - synthetic_table_totals[table]) / synthetic_population_size)

            pearson_r = stats.pearsonr(our_proportions, their_proportions).statistic

            # Make correlation negative so we can just minimise as normal
            return -1 * pearson_r, synthetic_counts

        def calculate_chi(error_households: [{dict}]):
            synthetic_counts = defaultdict(int)
            for error_household in error_households:
                for _, error_individual in error_household.items():
                    for error_characteristic in error_individual:
                        synthetic_counts[error_characteristic] += 1

            synthetic_table_totals = defaultdict(int)
            for characteristic, count in synthetic_counts.items():
                synthetic_table_totals[characteristic[:4]] += count

            synthetic_population_size = max(synthetic_table_totals.values())

            our_proportions = []
            chi_their_proportions = []
            # This for loop is performed in the same order as for the SAPS marginals
            for table, characteristics in tables_and_characteristics.items():
                for total_header, total_value in all_tables_totals.items():
                    if table in total_header:
                        tables_total = total_value
                        break

                # This for loop is performed in the same order as for the SAPS marginals
                for characteristic in characteristics:
                    if characteristic != "":
                        our_proportions.append(
                            synthetic_counts[characteristic])
                        chi_their_proportions.append(this_eds_aggregates[characteristic])
                    else:
                        our_proportions.append(
                            (synthetic_population_size - synthetic_table_totals[table]))
                        chi_their_proportions.append((population_to_normalise_to - tables_total))

            chi = stats.chi2_contingency(observed=(our_proportions, their_proportions)).statistic

            # Make correlation negative so we can just minimise as normal
            return chi, synthetic_counts

        # old_error, our_final_totals = calculate_correlation(potential_households)
        old_error, our_final_totals = calculate_error(potential_households)
        min_temperature = 5
        # error_stopping_criteria = 10
        error_stopping_criteria = num_households_in_ed
        # error_stopping_criteria = num_households_in_ed * 0.5
        # error_stopping_criteria = - 0.92
        # error_stopping_criteria = 700
        # error_stopping_criteria = 15
        # print(f"error_stopping_criteria: {error_stopping_criteria}")
        best_solution = None
        best_error = np.inf
        num_repeats_at_temp_1 = 0
        while True:
            if control_parameter < 1:
                control_parameter = 1
                num_repeats_at_temp_1 += 1
            num_iterations = int(1_000 // (0.1 * control_parameter))
            # num_iterations = int(5_000 // (0.1 * control_parameter))
            for _ in tqdm(range(num_iterations)):
                # for _ in range(num_iterations):
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
                # new_error, possible_final_totals = calculate_correlation(possible_new_households)
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

            # print(f"Temperature: {control_parameter}")
            print(f"Best Error: {best_error}")
            # break
            # if (control_parameter < min_temperature) or (best_error < error_stopping_criteria):
            if (best_error <= error_stopping_criteria) or (num_repeats_at_temp_1 > 20):
                break

        if "/" in ed:
            ed = ed.replace("/", "_")
        with open(results_folder + f"{ed}.pkl", "wb") as f:
            pkl.dump(best_solution, f)
        # print(f"\nED: {ed}")
        # print(f"Final error: {best_error}")
        # print("Characteristic counts: Ours | Theirs")
        # for ed_characteristic, ed_count in this_eds_aggregates.items():
        #     if ed_characteristic in error_columns:
        #         print(f"{ed_characteristic}: \t\t\t\t{our_final_totals[ed_characteristic]} | {ed_count}")

        # print(f"Pearson's R coefficient: {stats.pearsonr(ours, theirs)}")

        # print("\nHouseholds:")
        # for idx, household in enumerate(best_solution):
        #     print(f"Household {idx}")
        #     for individuals_id, individual in household.items():
        #         print(f"\tIndividual {individuals_id}")
        #         for error_column in individual.keys():
        #             if error_column != "others":
        #                 print(f"\t\t{individual[error_column]}")
        #     print("\n")



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

    eds = ed_aggregates["ED_ID"].unique()
    # eds = ["68003"] # Barna
    # eds = ["68013"] # Newcastle
    # eds = ["167065"] # Navan Rural
    # for ed in eds[:1]:
    for ed in eds:
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

        our_error_characteristic_counts = defaultdict(int)
        for _, household_characteristic_counts in admitted_households.items():
            for characteristic, count in household_characteristic_counts.items():
                our_error_characteristic_counts[characteristic] += count

        ours = []
        theirs = []
        print(f"\nED: {ed}")
        print("Characteristic counts: Ours | Theirs")
        for characteristic, count in our_error_characteristic_counts.items():
            print(f"\t{characteristic}: {count} | {this_eds_aggregates[characteristic]}")
            ours.append(count)
            theirs.append(this_eds_aggregates[characteristic])

        print(f"Pearson's R coefficient: {stats.pearsonr(ours, theirs)}")

        # for characteristic, count in quota_totals.items():
        #     print(f"{characteristic}: {count} left to fill")


if __name__ == '__main__':
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

    # ed_totals = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")
    # ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
    # new_employment_name_male = "T8_1_UNEM"
    # new_employment_name_female = "T8_1_UNEF"
    # detailed_unemployments_male = ["T8_1_LFFJM", "T8_1_STUM", "T8_1_LTUM"]
    # detailed_unemployments_female = ["T8_1_LFFJF", "T8_1_STUF", "T8_1_LTUF"]
    # ed_totals[new_employment_name_male] = ed_totals[detailed_unemployments_male].sum(axis=1)
    # ed_totals = ed_totals.drop(detailed_unemployments_male, axis=1)
    # ed_totals[new_employment_name_female] = ed_totals[detailed_unemployments_female].sum(axis=1)
    # ed_totals = ed_totals.drop(detailed_unemployments_female, axis=1)
    # ed_totals["ED_ID"] = ed_totals["ED_ID"].astype(str)

    ed_totals = pd.read_csv("rescaled_ed_aggregates_ordered.csv")
    ed_totals["ED_ID"] = ed_totals["ED_ID"].astype(str)

    # with open('2023q3_households_new_schema_more_constraints.pkl', 'rb') as f:
    #     q3_households = pkl.load(f)

    print(f"Num. households: {len(q3_households)}")

    # error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
    #               r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
    #               r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$|" \
    #               r"(^T5_2_)[^T].*P$"
    error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
                  r"(^T5_2_)[^T].*P$|" \
                  r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$"
    regex_match_string = re.compile(error_regex)
    error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

    simulated_annealing(households=q3_households, ed_aggregates=ed_totals, error_columns=error_columns)
    # quota_sampling(households=q3_households, ed_aggregates=ed_totals, error_columns=error_columns)
    # quota_sampling_configs(households=q3_households, ed_aggregates=ed_totals, error_columns=error_columns)



