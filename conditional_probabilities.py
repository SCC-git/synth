import itertools
import random
from collections import Counter, defaultdict
import numpy as np
from scipy.spatial import distance
import re
import pandas as pd
from tqdm import tqdm
from constants import tables_and_characteristics_with_nas, \
    saps_marital_statuses, \
    saps_ages, \
    sexes
import pickle as pkl
from lfs_status_converters import household_size, employment_status, highest_level_of_education


restarts = 0


def make_person(hierarchical_characteristics: dict, prefixes_probs: dict, prefix_to_proritise=None):
    global already_calculated_value_counts
    global already_calculated_hits

    persons_characteristics = []
    prefixes_done_already = []

    # Sample random header (uniform probability)
    if not prefix_to_proritise:
        prefix = random.sample(list(hierarchical_characteristics.keys()), 1)[0]
    else:
        prefix = prefix_to_proritise
    prefixes_done_already.append(prefix)

    # Sample random value
    persons_characteristics.append(np.random.choice(a=hierarchical_characteristics[prefix], size=1, p=prefixes_probs[prefix])[0])
    hierarchical_characteristics.pop(prefix, None)
    query_string = str(prefix) + "==" + repr(persons_characteristics[-1])

    while len(hierarchical_characteristics.keys()) > 0:
        # Sample random header (uniform probability)
        prefix = random.sample(list(hierarchical_characteristics.keys()), 1)[0]

        # TODO: Make this nicer
        if query_string in already_calculated_value_counts:
            if prefix in already_calculated_value_counts[query_string]:
                categorical_conditional_probs = already_calculated_value_counts[query_string][prefix]
                already_calculated_hits += 1
            else:
                categorical_conditional_probs = micro_df.query(query_string)[prefix].value_counts(normalize=True, dropna=False).to_dict()
                already_calculated_value_counts[query_string][prefix] = categorical_conditional_probs
        else:
            categorical_conditional_probs = micro_df.query(query_string)[prefix].value_counts(normalize=True, dropna=False).to_dict()
            already_calculated_value_counts[query_string] = {}
            already_calculated_value_counts[query_string][prefix] = categorical_conditional_probs

        keys = list(categorical_conditional_probs.keys())
        chosen = np.random.choice(a=keys, size=1, p=list(categorical_conditional_probs.values()))
        persons_characteristics.append(chosen[0])

        prefixes_done_already.append(prefix)

        query_string += " & " + str(prefix) + "==" + repr(persons_characteristics[-1])

        hierarchical_characteristics.pop(prefix, None)

    return persons_characteristics


if __name__ == '__main__':
    results_folder = "./results/conditional_probabilities/"

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

    ed_totals = pd.read_csv("rescaled_ed_aggregates_ordered.csv")

    error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T1_2).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T5_2_)[^T].*P$|" \
                  r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$|" \
                  r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$"
    regex_match_string = re.compile(error_regex)
    error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

    lfs_marginal_probs = {}
    for table, _ in tables_and_characteristics_with_nas.items():
        lfs_marginal_probs[table] = micro_df.groupby(table).size().div(len(micro_df))

    eds = ed_totals["ED_ID"].unique()

    for ed in tqdm(eds):
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

        tables_prefixes = ["T1_1", "T1_2", "T5_2", "T8_1", "T10_"]
        tables_totals = {}
        for prefix in tables_prefixes:
            prefix_regex = re.compile(rf"(^{prefix}).+$")
            tables_columns = sorted(list(filter(prefix_regex.match, list(this_eds_aggregates.keys()))))

            tables_total = 0
            for column in tables_columns:
                tables_total += this_eds_aggregates[column]
            tables_totals[prefix] = tables_total

        desired_population_size = max(tables_totals.values())

        js_distances = {}
        tables_probabilities = {}
        # Calculate Jensen-Shanon distance for each heading
        for table, characteristics in tables_and_characteristics_with_nas.items():
            ordered_lfs_marginals = []
            ordered_saps_marginals = []
            tables_marginals = lfs_marginal_probs[table]
            for characteristic in characteristics:
                ordered_lfs_marginals.append(tables_marginals[characteristic])
                ordered_saps_marginals.append(this_eds_aggregates[characteristic] / tables_totals[table])

            js_distances[table] = distance.jensenshannon(ordered_lfs_marginals, ordered_saps_marginals)
            tables_probabilities[table] = ordered_saps_marginals

        least_similar = max(js_distances, key=js_distances.get)

        already_calculated_value_counts = {}
        already_calculated_hits = 0

        population = []
        prioritisation_checkpoint = 0.3  # Percentage along the population where we want to start evaluating our synthetic distribution
        checkpoint_number = prioritisation_checkpoint * desired_population_size
        num_checkpoints = 10
        checkpoints = [int(k * round((desired_population_size - checkpoint_number) / num_checkpoints) + checkpoint_number)
                       for k in range(num_checkpoints)]

        for i in range(desired_population_size):
            if (i >= checkpoint_number) and (i in checkpoints):
                synthetic_characteristics = [i for i in list(itertools.chain.from_iterable(population))]
                synthetic_counter = Counter(synthetic_characteristics)

                synthetic_table_totals = defaultdict(int)
                for characteristic, count in synthetic_counter.items():
                    synthetic_table_totals[characteristic[:4]] += count

                current_synthetic_population_size = max(synthetic_table_totals.values())

                new_distances = {}
                # This for loop is performed in the same order as for the SAPS marginals
                for table, characteristics in tables_and_characteristics_with_nas.items():
                    ordered_synthetic_marginals = []
                    # This for loop is performed in the same order as for the SAPS marginals
                    for characteristic in characteristics:
                        ordered_synthetic_marginals.append(synthetic_counter[characteristic] / current_synthetic_population_size)

                    new_distances[table] = distance.jensenshannon(ordered_synthetic_marginals, tables_probabilities[table])

                least_similar = max(new_distances, key=new_distances.get)

            population.append(make_person(tables_and_characteristics_with_nas.copy(), tables_probabilities, prefix_to_proritise=least_similar))

        if "/" in ed:
            ed = ed.replace("/", "_")
        with open(results_folder + f"/{ed}.pkl", "wb") as f:
            pkl.dump(population, f)