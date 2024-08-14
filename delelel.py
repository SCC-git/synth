import pandas as pd
import re

sap_df = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")

new_names = ["T10_4_PLC", "T10_4_DGR"]
for sex in ["M", "F"]:
    qualis_to_combine = [
        [f"T10_4_TV{sex}", f"T10_4_ACCA{sex}"],  # PLC
        [f"T10_4_ODND{sex}", f"T10_4_HDPQ{sex}"]  # Degree
    ]

    name_idx = 0
    for list_of_equivalent_qualis in qualis_to_combine:
        new_name = new_names[name_idx] + sex

        sap_df[new_name] = sap_df[list_of_equivalent_qualis].sum(axis=1)
        sap_df = sap_df.drop(list_of_equivalent_qualis, axis=1)
        name_idx += 1


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
#         sap_df[name_to_rebrand_as] = sap_df[age_combo].sum(axis=1)
#         sap_df = sap_df.drop(age_combo, axis=1)
#
# age_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!F)$"
# regex_match_string = re.compile(age_regex)
# matches = sorted(list(filter(regex_match_string.match, sap_df.columns)))

sap_df.to_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")

print(1)