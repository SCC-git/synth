import itertools
import random
from collections import Counter, defaultdict
# from math import isnan
import numpy as np
from scipy.spatial import distance
import re
import pandas as pd
from tqdm import tqdm
from scipy import stats
from constants import tables_and_characteristics_with_nas, \
    saps_marital_statuses, \
    saps_levels_of_education, \
    saps_ages, \
    saps_employment_statuses, \
    sexes
import pickle as pkl
from os import listdir
from lfs_status_converters import household_size, employment_status, highest_level_of_education


restarts = 0

def get_population_proportions(p):
    pass


def make_person(hierarchical_characteristics: dict, prefixes_probs: dict, prefix_to_proritise=None):
    global already_calculated_value_counts
    global already_calculated_hits
    characteristics = []
    prefixes_done_already = []

    # Sample random header (uniform probability)
    if not prefix_to_proritise:
        prefix = random.sample(list(hierarchical_characteristics.keys()), 1)[0]
    else:
        prefix = prefix_to_proritise
    # prefix = "T8_1"
    prefixes_done_already.append(prefix)
    # for header, headers_total in tables_totals.items():
    #     if prefix in header:
    #         prefixes_total = headers_total
    #         break
    # for header, header_count in all_tables_totals.items():
    #     if prefix in header:
    #         prefixes_total = header_count
    #         break
    #
    # prefixes_probs = []
    # for v in hierarchical_characteristics[prefix]:
    #     if v != "":
    #         prefixes_probs.append(this_eds_aggregates[v] / population_to_normalise_to)
    #     else:
    #         prefixes_probs.append((population_to_normalise_to - prefixes_total) / population_to_normalise_to)
    # Sample random value TODO: probability from ED distributions
    characteristics.append(np.random.choice(a=hierarchical_characteristics[prefix], size=1, p=prefixes_probs[prefix])[0])
    hierarchical_characteristics.pop(prefix, None)
    query_string = str(prefix) + "==" + repr(characteristics[-1])

    # for _ in range(len(hierarchical_characteristics.keys())):
    while len(hierarchical_characteristics.keys()) > 0:
        # Sample random header (uniform probability)
        prefix = random.sample(list(hierarchical_characteristics.keys()), 1)[0]
        # prefixes_done_already.append(prefix)

        # Sample random value TODO: probability from LFS conditional distributions
        # conditional_probs = micro_df.groupby(prefixes_done_already).size().div(len(micro_df)).div(marginals[])
        # categorical_conditional_probs = micro_df.groupby(prefixes_done_already)[prefix].value_counts(normalize=True, dropna=False)
        # categorical_conditional_probs = micro_df[(micro_df[prefixes_done_already[-1]] == characteristics[-1])][prefix].value_counts(normalize=True, dropna=False)
        # TODO: Make this nicer
        if query_string in already_calculated_value_counts:
            if prefix in already_calculated_value_counts[query_string]:
                categorical_conditional_probs = already_calculated_value_counts[query_string][prefix]
                already_calculated_hits += 1
            else:
                categorical_conditional_probs = micro_df.query(query_string)[prefix].value_counts(normalize=True, dropna=False).to_dict()
                # if isinstance(already_calculated_value_counts[query_string], dict):
                #     already_calculated_value_counts[query_string][prefix] = categorical_conditional_probs
                # else:
                #     already_calculated_value_counts[query_string] = {}
                already_calculated_value_counts[query_string][prefix] = categorical_conditional_probs
        else:
            categorical_conditional_probs = micro_df.query(query_string)[prefix].value_counts(normalize=True, dropna=False).to_dict()
            already_calculated_value_counts[query_string] = {}
            already_calculated_value_counts[query_string][prefix] = categorical_conditional_probs
        # if (query_string in already_calculated_value_counts) and (prefix in already_calculated_value_counts[query_string]):
        #     categorical_conditional_probs = already_calculated_value_counts[query_string][prefix]
        #     already_calculated_hits += 1
        # else:
        #     categorical_conditional_probs = micro_df.query(query_string)[prefix].value_counts(normalize=True, dropna=False).to_dict()
        #     if isinstance(already_calculated_value_counts[query_string], dict):
        #         already_calculated_value_counts[query_string][prefix] = categorical_conditional_probs
        #     else:
        #         already_calculated_value_counts[query_string] = {}
        #         already_calculated_value_counts[query_string][prefix] = categorical_conditional_probs

        # Combination of characteristics is not possible, restart
        # if len(categorical_conditional_probs) < 1:
        #     global restarts
        #     restarts += 1
        #     print(f"Restart counter: {restarts}")
        #     make_person(tables_and_characteristics.copy())
        # our_conditional_probs = categorical_conditional_probs[characteristics].to_dict()
        # conditional_probs = conditional_probs[characteristics]
        # characteristics.append(np.random.choice(hierarchical_characteristics[prefix], 1, p=prefixes_probs)[0])
        # characteristics_by_conditional_probability = [k[-1] for k in categorical_conditional_probs.keys()]
        keys = list(categorical_conditional_probs.keys())
        chosen = np.random.choice(a=keys, size=1, p=list(categorical_conditional_probs.values()))
        characteristics.append(chosen[0])

        prefixes_done_already.append(prefix)

        query_string += " & " + str(prefix) + "==" + repr(characteristics[-1])

        hierarchical_characteristics.pop(prefix, None)

    return characteristics




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
    # micro_df["T10_"] = micro_df.apply(lambda row: saps_levels_of_education[row["HATLEVEL"]] + sexes[row["SEX"]], axis=1)
    micro_df["T10_"] = micro_df.apply(highest_level_of_education, axis=1)

    # probs = micro_df.value_counts(["SEX", "AGECLASS", "MARSTAT", "HATLEVEL", "NATUREOFOCCUPANCY", "MAINSTAT"], normalize=True, dropna=False)
    # probs = probs.to_dict()

    ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
    new_employment_name_male = "T8_1_UNEM"
    new_employment_name_female = "T8_1_UNEF"
    detailed_unemployments_male = ["T8_1_LFFJM", "T8_1_STUM", "T8_1_LTUM"]
    detailed_unemployments_female = ["T8_1_LFFJF", "T8_1_STUF", "T8_1_LTUF"]
    ed_totals[new_employment_name_male] = ed_totals[detailed_unemployments_male].sum(axis=1)
    ed_totals = ed_totals.drop(detailed_unemployments_male, axis=1)
    ed_totals[new_employment_name_female] = ed_totals[detailed_unemployments_female].sum(axis=1)
    ed_totals = ed_totals.drop(detailed_unemployments_female, axis=1)
    ed_totals["ED_ID"] = ed_totals["ED_ID"].astype(str)

    # with open("adult_predicates_house_size.pkl", "rb") as f:
    #     adults = pkl.load(f)
    # with open("children_predicates_house_size.pkl", "rb") as f:
    #     children = pkl.load(f)

    error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
                  r"(^T5_2_)[^T].*P$|" \
                  r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$"

    regex_match_string = re.compile(error_regex)
    error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

    lfs_marginal_probs = {}
    for table, _ in tables_and_characteristics_with_nas.items():
        lfs_marginal_probs[table] = micro_df.groupby(table).size().div(len(micro_df))

    column_to_normalise_off = "T5_2_TP"

    # eds = ["167065"] # Navan Rural
    # eds = ["68013"] # Newcastle
    # eds = ["68003"] # Barna
    eds = ed_totals["ED_ID"].unique()
    # eds = ["47298", "147008", "147019"]

    results_folder = "./results/mine/"

    files = [f.split(".")[0] for f in listdir(results_folder)]

    # for ed in eds[:1]:
    # for ed in eds[1025:]:
    for ed in tqdm(eds):
        if "/" in ed:
            id_for_lookup = ed.replace("/", "_")
        else:
            id_for_lookup = ed
        if id_for_lookup in files:
            continue

        this_eds_aggregates = ed_totals[ed_totals["ED_ID"] == str(ed)].to_dict('records')
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

        # table_prefixes = ["T1_1", "T1_2", "T5_2", "T8_1", "T10_"]
        table_prefixes_to_normalise = ["T1_1", "T1_2", "T8_1", "T10_"]
        # tables_totals = ["T1_1AGETT", "T1_2T", "T5_2_TP", "T8_1_TT", "T10_4_TT"]  # Don't think we need to rescale T5_2
        tables_totals_to_normalise = ["T1_1AGETT", "T1_2T", "T8_1_TT", "T10_4_TT"]  # Don't think we need to rescale T5_2

        population_to_normalise_to = this_eds_aggregates[column_to_normalise_off]
        present = this_eds_aggregates["T1_1AGETT"]
        for tot in tables_totals_to_normalise:
            this_eds_aggregates[tot] = round(this_eds_aggregates[tot] * (population_to_normalise_to / present))
        # rescaled_totals = [round(tot * (usually_residents / present)) for tot in tables_totals]

        for i, prefix in enumerate(table_prefixes_to_normalise):
            # Based off Bresenham's line drawing algorithm
            # https://stackoverflow.com/a/31121856s
            columns_with_prefix = {k: v for k, v in this_eds_aggregates.items()
                                   if (prefix in k) and (k in error_columns)}
            unnormalised_sum = sum(columns_with_prefix.values())
            rem = 0
            for characteristic, total in columns_with_prefix.items():
                count = total * this_eds_aggregates[tables_totals_to_normalise[i]] + rem
                this_eds_aggregates[characteristic] = count // unnormalised_sum
                rem = count % unnormalised_sum
            this_eds_aggregates[random.sample(columns_with_prefix.keys(), 1)[0]] += rem

        # table_prefixes = ["T1_1", "T1_2", "T8_1", "T10_"]
        # table_prefixes = ["T1_1", "T1_2", "T5_2", "T8_1", "T10_"]
        #
        # tables_and_characteristics = defaultdict(list)
        # for characteristic, _ in this_eds_aggregates.items():
        #     if characteristic in error_columns:
        #         for prefix in table_prefixes:
        #             if prefix in characteristic:
        #                 tables_and_characteristics[prefix].append(characteristic)
        #
        # tables_and_characteristics = dict(tables_and_characteristics)

        all_tables_totals_headers = ["T1_1AGETT", "T1_2T", "T5_2_TP", "T8_1_TT", "T10_4_TT"]
        all_tables_totals = {}
        for total in all_tables_totals_headers:
            all_tables_totals[total] = this_eds_aggregates[total]

        js_distances = {}
        tables_probabilities = {}
        # Calculate Jensen-Shanon distance for each heading
        for table, characteristics in tables_and_characteristics_with_nas.items():
            # Get total value of table
            for total_header, total_value in all_tables_totals.items():
                if table in total_header:
                    tables_total = total_value
                    break

            ordered_lfs_marginals = []
            ordered_saps_marginals = []
            tables_marginals = lfs_marginal_probs[table]
            for characteristic in characteristics:
                ordered_lfs_marginals.append(tables_marginals[characteristic])
                if characteristic != "":
                    ordered_saps_marginals.append(this_eds_aggregates[characteristic] / population_to_normalise_to)
                else:
                    ordered_saps_marginals.append((population_to_normalise_to - tables_total) / population_to_normalise_to)

            js_distances[table] = distance.jensenshannon(ordered_lfs_marginals, ordered_saps_marginals)
            tables_probabilities[table] = ordered_saps_marginals

        least_similar = max(js_distances, key=js_distances.get)
        # print(f"Initially prioritising: {least_similar}")

        already_calculated_value_counts = {}
        already_calculated_hits = 0

        population = []
        prioritisation_checkpoint = 0.3  # Percentage along the population where we want to start evaluating our synthetic distribution
        checkpoint_number = prioritisation_checkpoint * population_to_normalise_to
        # prioritisation_intervals = 5  # In percent of population
        num_checkpoints = 10
        checkpoints = [int(k * round((population_to_normalise_to - checkpoint_number) / num_checkpoints) + checkpoint_number)
                       for k in range(num_checkpoints)]
        # checkpoints = [int(k * round((population_to_normalise_to - checkpoint_number) / 10) + checkpoint_number)
        #                for k in range(10)]
        # for i in tqdm(range(population_to_normalise_to)):
        for i in range(population_to_normalise_to):
            if (i >= checkpoint_number) and (i in checkpoints):
                # for person in population:
                #     if "" in person:
                #         if any(t10 in person for t10 in tables_and_characteristics["T10_"]):

                synthetic_characteristics = [i for i in list(itertools.chain.from_iterable(population))]
                synthetic_counter = Counter(synthetic_characteristics)

                synthetic_table_totals = defaultdict(int)
                for characteristic, count in synthetic_counter.items():
                    synthetic_table_totals[characteristic[:4]] += count

                synthetic_population_size = max(synthetic_table_totals.values())

                new_distances = {}
                # This for loop is performed in the same order as for the SAPS marginals
                for table, characteristics in tables_and_characteristics_with_nas.items():
                    ordered_synthetic_marginals = []
                    # synthetic_table_total = synthetic_table_totals[table]
                    # This for loop is performed in the same order as for the SAPS marginals
                    for characteristic in characteristics:
                        if characteristic != "":
                            ordered_synthetic_marginals.append(
                                synthetic_counter[characteristic] / synthetic_population_size)
                                # synthetic_counter[characteristic] / synthetic_table_totals[characteristic[:4]])
                        else:
                            ordered_synthetic_marginals.append(
                                (synthetic_population_size - synthetic_table_totals[table]) / synthetic_population_size)
                                # (population_to_normalise_to - synthetic_table_total) / population_to_normalise_to)

                    new_distances[table] = distance.jensenshannon(ordered_synthetic_marginals, tables_probabilities[table])

                least_similar = max(new_distances, key=new_distances.get)
                # print(f"Checkpoint: {i} | Prioritising: {least_similar}")

            population.append(make_person(tables_and_characteristics_with_nas.copy(), tables_probabilities, prefix_to_proritise=least_similar))

        # population = [make_person(tables_and_characteristics.copy(), tables_probabilities, prefix_to_proritise=least_similar)
        #               for _ in tqdm(range(population_to_normalise_to))]

        if "/" in ed:
            ed = ed.replace("/", "_")
        with open(f"./results/mine/{ed}.pkl", "wb") as f:
            pkl.dump(population, f)

        # our_error_characteristic_counts = defaultdict(int)
        # for person in population:
        #     for characteristic in person:
        #         # if characteristic in ["T8_1_SM", "T8_1_SF"]:
        #         #     print(person)
        #         our_error_characteristic_counts[characteristic] += 1
        #
        # synthetic_characteristics = [i for i in list(itertools.chain.from_iterable(population))]
        # synthetic_counter = Counter(synthetic_characteristics)
        #
        # synthetic_table_totals = defaultdict(int)
        # for characteristic, count in synthetic_counter.items():
        #     synthetic_table_totals[characteristic[:4]] += count
        #
        # synthetic_population_size = max(synthetic_table_totals.values())
        #
        # final_proportions = {}
        # our_proportions = []
        # their_proportions = []
        # # This for loop is performed in the same order as for the SAPS marginals
        # for table, characteristics in tables_and_characteristics.items():
        #     final_proportions[table] = []
        #     # synthetic_table_total = synthetic_table_totals[table]
        #     # This for loop is performed in the same order as for the SAPS marginals
        #     for characteristic in characteristics:
        #         if characteristic != "":
        #             final_proportions[table].append(
        #                 synthetic_counter[characteristic] / synthetic_population_size)
        #             # synthetic_counter[characteristic] / synthetic_table_totals[characteristic[:4]])
        #         else:
        #             final_proportions[table].append(
        #                 (synthetic_population_size - synthetic_table_totals[table]) / synthetic_population_size)
        #     our_proportions.extend(final_proportions[table])
        #     their_proportions.extend(tables_probabilities[table])
        #
        # print(f"Pearson's R coefficient (proportions): {stats.pearsonr(our_proportions, their_proportions)}")
        #
        # print("\nCharacteristic counts: Ours | Theirs")
        # topic_counts = {}
        # eds_aggregates_by_topic = {}
        # total_error = 0
        # ours = []
        # theirs = []
        # for ed_characteristic, ed_count in this_eds_aggregates.items():
        #     if ed_characteristic in error_columns:
        #         print(f"{ed_characteristic}: \t\t\t\t{our_error_characteristic_counts[ed_characteristic]} | {ed_count}")
        #         ours.append(our_error_characteristic_counts[ed_characteristic])
        #         theirs.append(ed_count)
        #
        #         total_error += abs(our_error_characteristic_counts[ed_characteristic] - ed_count)
        #
        #         if ed_characteristic[:4] in topic_counts:
        #             topic_counts[ed_characteristic[:4]] += our_error_characteristic_counts[ed_characteristic]
        #         else:
        #             topic_counts[ed_characteristic[:4]] = our_error_characteristic_counts[ed_characteristic]
        #
        #         if ed_characteristic[:4] in eds_aggregates_by_topic:
        #             eds_aggregates_by_topic[ed_characteristic[:4]] += ed_count
        #         else:
        #             eds_aggregates_by_topic[ed_characteristic[:4]] = ed_count
        #
        # print(f"\nTotal error: {total_error}")
        # print(f"Pearson's R coefficient (raw numbers): {stats.pearsonr(ours, theirs)}")
        #
        # print("\nTopics")
        # print("Characteristic: Ours | Theirs")
        # for topic, topic_count in topic_counts.items():
        #     print(f"{topic}: {topic_count} | {eds_aggregates_by_topic[topic]}")
        #
        # print(f"Times we used cached value_counts: {already_calculated_hits}")



