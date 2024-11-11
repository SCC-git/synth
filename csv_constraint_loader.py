import re
import random
import pandas as pd
from tqdm import tqdm

from constants import tables_and_characteristics_with_nas

# ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
ed_totals = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")

new_names = ["T10_4_PLC", "T10_4_DGR"]
for sex in ["M", "F"]:
    qualis_to_combine = [
        [f"T10_4_TV{sex}", f"T10_4_ACCA{sex}"],  # PLC
        [f"T10_4_ODND{sex}", f"T10_4_HDPQ{sex}"]  # Degree
    ]

    name_idx = 0
    for list_of_equivalent_qualis in qualis_to_combine:
        new_name = new_names[name_idx] + sex

        ed_totals[new_name] = ed_totals[list_of_equivalent_qualis].sum(axis=1)
        ed_totals = ed_totals.drop(list_of_equivalent_qualis, axis=1)
        name_idx += 1

    new_employment_name = "T8_1_UNE" + sex
    detailed_unemployments = [f"T8_1_LFFJ{sex}", f"T8_1_STU{sex}", f"T8_1_LTU{sex}"]
    ed_totals[new_employment_name] = ed_totals[detailed_unemployments].sum(axis=1)
    ed_totals = ed_totals.drop(detailed_unemployments, axis=1)

    new_marital_status_name = "T1_2SEP" + sex
    detailed_maritals = [f"T1_2SEP{sex}", f"T1_2DIV{sex}"]
    new_marital_df = pd.DataFrame({new_marital_status_name: ed_totals[detailed_maritals].sum(axis=1)})
    ed_totals.update(new_marital_df)

ed_totals["ED_ID"] = ed_totals["ED_ID"].astype(str)

# r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
              r"(^T1_2).+(?<!T)(?<!TM)(?<!TF)$|" \
              r"(^T5_2_)[^T].*P$|" \
              r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$|" \
              r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$"

regex_match_string = re.compile(error_regex)
error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

eds = ed_totals["ED_ID"].unique()

column_to_normalise_off = "T5_2_TP"

to_save = {}
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

    table_prefixes_to_normalise = ["T1_1", "T1_2", "T8_1", "T10_"]
    tables_totals_to_normalise = ["T1_1AGETT", "T1_2T", "T8_1_TT", "T10_4_TT"]  # Don't think we need to rescale T5_2

    population_to_normalise_to = this_eds_aggregates[column_to_normalise_off]
    present = this_eds_aggregates["T1_1AGETT"]
    for tot in tables_totals_to_normalise:
        this_eds_aggregates[tot] = round(this_eds_aggregates[tot] * (population_to_normalise_to / present))

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
        this_eds_aggregates[random.sample(list(columns_with_prefix.keys()), 1)[0]] += rem

        # Add in NAs
        if this_eds_aggregates[tables_totals_to_normalise[i]] < population_to_normalise_to:
            if prefix == "T10_":
                prefix = "T10_4"
            this_eds_aggregates[prefix + "_NA"] = population_to_normalise_to - this_eds_aggregates[tables_totals_to_normalise[i]]
            error_columns.append(prefix + "_NA")

    for key, value in this_eds_aggregates.items():
        if key in error_columns or key in ["ED_ID", "GEOGDESC"]:
            if key not in to_save:
                to_save[key] = [value]
            else:
                to_save[key].append(value)

desired_order_of_columns = ["GEOGDESC", "ED_ID"]
for table, characteristics in tables_and_characteristics_with_nas.items():
    desired_order_of_columns.extend(sorted(characteristics))

df = pd.DataFrame.from_dict(to_save)

ordered_df = df[desired_order_of_columns]

# print("Done")
ordered_df.to_csv("rescaled_ed_aggregates_ordered.csv", index=False)