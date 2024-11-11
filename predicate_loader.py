import copy
import itertools
import math
import numpy as np
import pandas as pd
import re
from tqdm import tqdm
import pickle as pkl


df = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
# ed_id_df = pd.read_csv("CSO_Electoral_Divisions_-_National_Statistical_Boundaries_-_2022_-_Generalised_100m.csv")
# ed_id_df = ed_id_df[["ED_GUID", "ED_ENGLISH", "ED_ID_STR", "COUNTY_ENGLISH"]]

column_strings_to_match = [
    # NOT INCLUDING TOTALS FOR ANY OF THESE
    r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$",  # Age and Sex (18+)
    r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$",  # Marital Status
    # r"(^T2_1)[^T].*C$",  # Citizenship
    # r"(^T2_2)[^T].*",  # Ethnicity
    # r"(^T2_4)[^T].*",  # Religion
    # r"(^T3_1)[^T].*",  # Irish speaking ability
    # r"(^T5_1)[^T].*P$",  # Household Type (persons only for now) TODO: Include households?
    r"(^T5_2_)[^T].*P$",  # Household Size (persons only for now)
    # r"(^T6_3_)[^T].*P$",  # Household Type of Occupancy (persons only for now)
    r"(^T8_1).+(?<!T)(?<!TM)(?<!TF)$",  # Principal Economic Status
    r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$",  # Highest Level of Education Completed (15 or over)
    # r"(^T12_1_)[^T]"  # Disability by sex
    # r"(^T12_3).+(?<!T)(?<!TM)(?<!TF)$"  # General Health by sex
]

regex_match_string = f"({'|'.join(column_strings_to_match)})"
regex_match_string = re.compile(regex_match_string)

columns = list(filter(regex_match_string.match, df.columns))
# columns.insert(0, "GUID")
# columns.insert(1, "GEOGDESC")

df = df[columns]

new_employment_name_male = "T8_1_UNEM"
new_employment_name_female = "T8_1_UNEF"
detailed_unemployments_male = ["T8_1_LFFJM", "T8_1_STUM", "T8_1_LTUM"]
detailed_unemployments_female = ["T8_1_LFFJF", "T8_1_STUF", "T8_1_LTUF"]
df[new_employment_name_male] = df[detailed_unemployments_male].sum(axis=1)
df = df.drop(detailed_unemployments_male, axis=1)
df[new_employment_name_female] = df[detailed_unemployments_female].sum(axis=1)
df = df.drop(detailed_unemployments_female, axis=1)

# id_strings = []
# index_to_remove = 0
# for idx, row in df.iterrows():
#     if row["GUID"] not in ed_id_df["ED_GUID"].values:
#         print(f"{row['GUID']} not in ED_ID dataframe")
#         print("KICKING IT OUT\n")
#         index_to_remove = idx
#     else:
#         id_strings.append(ed_id_df.loc[(ed_id_df["ED_GUID"] == row["GUID"]), "ED_ID_STR"].values[0])

# df = df.drop(index_to_remove)
#
# df = df.assign(ED_ID=id_strings)
#
# print(f"{df.iloc[3419]}")

# # Combine qualifications
# for sex in ["M", "F"]:
#     qualis_to_combine = [
#         [f"T10_4_P{sex}", f"T10_4_LS{sex}"],  # junior_cert_and_below
#         [f"T10_4_ACCA{sex}", f"T10_4_HC{sex}"],  # level_six_certificates
#         [f"T10_4_US{sex}", f"T10_4_NS{sex}"],  # leaving_cert_and_not_stated
#         [f"T10_4_ODND{sex}", f"T10_4_HDPQ{sex}", f"T10_4_PD{sex}", f"T10_4_D{sex}"]  # uni_degrees
#     ]
#     for quali_combo in qualis_to_combine:
#         split_name = quali_combo[0].split(sex)
#         name_to_rebrand_as = ''.join(split_name[:-1]) + "COMB" + sex
#         # quali_combo_first_name = quali_combo[0]
#         # df
#         # df = df.assign(quali_combo_first_name=df[quali_combo].sum(axis=1)).drop(quali_combo, 1)
#         df[name_to_rebrand_as] = df[quali_combo].sum(axis=1)
#         df = df.drop(quali_combo, axis=1)
#         # for individual_quali in quali_combo:
#         #     print(f"Removing {individual_quali} column")
#         #     df = df.drop(individual_quali, axis=1)

# # Group children and teenagers
# for sex in ["M", "F"]:
#     ages_to_combine = [
#         [f"T1_1AGE{age}{sex}" for age in range(0, 5)],
#         [f"T1_1AGE{age}{sex}" for age in range(5, 10)],
#         [f"T1_1AGE{age}{sex}" for age in range(10, 15)],
#         [f"T1_1AGE{age}{sex}" for age in range(15, 20)]
#     ]
#     for age_combo in ages_to_combine:
#         split_name = age_combo[0].split(sex)
#         if split_name[0][-2:].isdigit():
#             name_to_rebrand_as = ''.join(split_name[0]) + f"_{int(split_name[0][-2:]) + 4}" + sex
#         else:
#             name_to_rebrand_as = ''.join(split_name[0]) + f"_{int(split_name[0][-1]) + 4}" + sex
#
#         df[name_to_rebrand_as] = df[age_combo].sum(axis=1)
#         df = df.drop(age_combo, axis=1)

table_var_counts = {}
tables_by_topic = {}
for column in df.columns:
    # Count variables
    if column.startswith("T"):
        prefix = column[:4]
        if prefix not in table_var_counts:
            table_var_counts[prefix] = 1
            tables_by_topic[prefix] = [column]
        else:
            table_var_counts[prefix] += 1
            tables_by_topic[prefix].append(column)

# Things only counted for the usually resident
# Type of Occupancy - can be blank for people in temporary private households
# tables_by_topic["T6_3"].append("")

# usually_resident_but_not_present_topics = ["T5_1", "T5_2"]  #, "T6_3"]
usually_resident_but_not_present_topics = ["T5_2"]  #, "T6_3"]
# usually_resident_but_not_present_topics = ["T5_1", "T6_3"]
usually_resident_but_not_present_tables_by_topic = {topic: tables_by_topic[topic] for topic in
                                                    usually_resident_but_not_present_topics}
_, usually_resident_but_not_present_values = zip(*usually_resident_but_not_present_tables_by_topic.items())
usually_resident_but_not_present_predicates = itertools.product(*usually_resident_but_not_present_values)
for jvks in usually_resident_but_not_present_predicates:
    print(jvks)

# Housing Type
# tables_by_topic["T5_1"].append("")  # Not in private household
# House Size
tables_by_topic["T5_2"].append("")  # Not in private household

# Things only counted for the usually resident and present
# Ethnicity
# tables_by_topic["T2_2"].append("")
# tables_by_topic["T8_1"].remove("T8_1_SM")
# tables_by_topic["T8_1"].remove("T8_1_SF")

# Things only counted for only the present
# Allow for people without a primary economic status (kids)
# tables_by_topic["T8_1"].append("")
# Allow for people without a level of education completed (kids, students, etc)
tables_by_topic["T10_"].append("")

# single_stated_ethnicities = copy.deepcopy(tables_by_topic["T2_2"])
# single_stated_ethnicities.remove("T2_2NS")
# mixed_ethnicities = [''.join(ethnicities) for ethnicities in itertools.combinations(single_stated_ethnicities, 2)]
# tables_by_topic["T2_2"].extend(mixed_ethnicities)
# # Allow for people without an ethnicity (they can for some reason)
# tables_by_topic["T2_2"].append("")

topics, categorical_list_of_columns = zip(*tables_by_topic.items())
# predicates = [v for v in itertools.product(*values)]

childrens_ages = [f"T1_1AGE0_4M",
                  f"T1_1AGE5_9M",
                  f"T1_1AGE10_14M",
                  f"T1_1AGE0_4F",
                  f"T1_1AGE5_9F",
                  f"T1_1AGE10_14F"
                  ]

male_children_values = []
female_children_values = []
for idx, category in enumerate(categorical_list_of_columns):
    male_children_values.append([])
    female_children_values.append([])

    category_prefix = category[0][:4]

    # if idx == 0:
    if category_prefix == "T1_1":
        for column in category:
            if column in childrens_ages:
                if column[-1] == "M":
                    male_children_values[-1].append(column)
                elif column[-1] == "F":
                    female_children_values[-1].append(column)
    # elif idx == 1:
    elif category_prefix == "T1_2":
        male_children_values[-1].append("T1_2SGLM")
        female_children_values[-1].append("T1_2SGLF")
    # elif idx in [5, 6]:
    # elif idx == 5:
    # elif idx == 2:
    elif category_prefix == "T5_2":
        for column in category:
            if column != "T5_2_1PP": # Children can't live alone
                male_children_values[-1].append(column)
                female_children_values[-1].append(column)
    # elif idx == 3:
    elif category_prefix == "T8_1":
        male_children_values[-1].append("")
        female_children_values[-1].append("")
        # housing_possibilities = copy.deepcopy(category)
        # housing_possibilities.remove("T5_1OP_P")
        # housing_possibilities.remove("T5_1MC_P")
        # housing_possibilities.remove("T5_1CC_P")
        # male_children_values[-1].extend(housing_possibilities)
        # female_children_values[-1].extend(housing_possibilities)
    elif category_prefix == "T10_":
        male_children_values[-1].append("")
        female_children_values[-1].append("")
    else:
        print("Something went wrong")
        # for column in category:
        #     if column:
        #         if column[-1] == "M":
        #             male_children_values[-1].append(column)
        #         elif column[-1] == "F":
        #             female_children_values[-1].append(column)
        #         else:
        #             male_children_values[-1].append(column)
        #             female_children_values[-1].append(column)
        #     else:
        #         male_children_values[-1].append(column)
        #         female_children_values[-1].append(column)

for childrens_age in childrens_ages:
    tables_by_topic["T1_1"].remove(childrens_age)

male_adult_values = []
female_adult_values = []
for idx, category in enumerate(categorical_list_of_columns):
    male_adult_values.append([])
    female_adult_values.append([])
    for column in category:
        if len(column) > 0:
            # if idx == 3:
            #     if column == "T5_1OPFCO_P": # One parent household - father
            #         male_adult_values[-1].append(column)
            #         continue
            #     elif column == "T5_1OPMCO_P": # One parent household - mother
            #         female_adult_values[-1].append(column)
            #         continue
            if column[-1] == "M":
                male_adult_values[-1].append(column)
            elif column[-1] == "F":
                female_adult_values[-1].append(column)
            else:
                male_adult_values[-1].append(column)
                female_adult_values[-1].append(column)
        else:
            male_adult_values[-1].append(column)
            female_adult_values[-1].append(column)

not_temporarily_residents = [male_children_values,
                             female_children_values,
                             male_adult_values,
                             female_adult_values]

# students = [[], []]
# for idx, not_temporarily_resident in enumerate(not_temporarily_residents[2:]):
#     students[idx] = copy.deepcopy(not_temporarily_resident)
#     students[idx][5] = ["T8_1_S" + not_temporarily_resident[0][0][-1]]
#     # students[idx][6] = [""]

# not_temporarily_residents.extend(students)

# for category in categorical_list_of_columns:
#     if category[0][:4] == "T5_2": # House Size
#
# temporarily_residents = [[] for _ in range(len(categorical_list_of_columns.keys()))]
#
# for idx, not_temporarily_resident in enumerate(not_temporarily_residents):
#     temporarily_residents[idx] = copy.deepcopy(not_temporarily_resident)
#     temporarily_residents[idx][2] = [""]
#     temporarily_residents[idx][3] = [""]
#     temporarily_residents[idx][4] = [""]

non_temporary_predicates = [itertools.product(*not_temporarily_resident)
                            for not_temporarily_resident in not_temporarily_residents]

# student_predicates = [itertools.product(*student) for student in students]

# temporary_predicates = [itertools.product(*temporarily_resident)
#                         for temporarily_resident in temporarily_residents]


validities = {"predicate": []}
for category in categorical_list_of_columns:
    for column in category:
        validities[column] = []

# all_types_of_predicate = [valid_male_present_predicates,
#                           valid_female_present_predicates,
#                           usually_resident_but_not_present_predicates]

temp_and_non_temp_predicates = [non_temporary_predicates] # ,
                                # [usually_resident_but_not_present_predicates]]

# t6_3s = ["T6_3_OMLP",
#          "T6_3_OOP",
#          "T6_3_RPLP",
#          "T6_3_RLAP",
#          "T6_3_RVCHBP",
#          "T6_3_OFRP",
#          "T6_3_NSP"]
for temp_or_non_temp in temp_and_non_temp_predicates:
    for type_of_predicate in temp_or_non_temp:
        for valid_predicate in tqdm(type_of_predicate):
            # joined_predicate = '_'.join(valid_predicate)
            # if ("T6_3" in joined_predicate) and ("T5_1" not in joined_predicate):
            #     invalid_house_count += 1
            #     continue
            # validities["predicate"].append(joined_predicate)
            validities["predicate"].append(valid_predicate)
            for column in validities.keys():
                if column == "predicate":
                    continue
                if column in valid_predicate:
                    validities[column].append(True)
                else:
                    validities[column].append(False)

# print(f"invalid_house_count: {invalid_house_count}")

# for usually_resident_but_not_present_predicate in tqdm(usually_resident_but_not_present_predicates):
#     validities["predicate"].append('_'.join(usually_resident_but_not_present_predicate))
#     for column in validities.keys():
#         if column == "predicate":
#             continue
#         if column in usually_resident_but_not_present_predicate:
#             validities[column].append(True)
#         else:
#             validities[column].append(False)


constraints_df = pd.DataFrame(validities)

all_predicates = list(constraints_df["predicate"].unique())
for house_size in tables_by_topic["T5_2"]:
    if house_size != "":
        all_predicates.append([house_size])
# for usually_resident_but_not_present_predicate in usually_resident_but_not_present_predicates:
#     all_predicates.append(usually_resident_but_not_present_predicate)

with open("all_predicates.pkl", "wb") as f:
    pkl.dump(all_predicates, f)

# constraints_df.to_csv("different_populations_new_constraints.csv")

# df.to_csv("different_populations_new_cleaned_aggregates.csv")

# print(table_var_counts)
# print(f"Number of combos: {math.prod(table_var_counts.values())}")

