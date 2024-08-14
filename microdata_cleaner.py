import pickle
import re
import pandas as pd
from constants import saps_ages, saps_marital_statuses, saps_levels_of_education
from tqdm import tqdm
import pickle as pkl
from collections import Counter

folder = "0061-00 LFS_Q11998-Q32023/0061-00 LFS/0061-00_Data/CSV/"
file = "0061-24_lfs_2023.csv"

micro_df = pd.read_csv(folder + file)
grouped = micro_df.groupby(["refperiod", "QHHNUM"])
# q3_df = micro_df[micro_df["refperiod"] == "2023Q3"]
sap_df = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")

quarter_to_study = "2023Q3"
micro_columns = list(micro_df.columns)

# Get size of each household for Quota Sampling
num_people_in_each_household = Counter(micro_df["QHHNUM"].tolist())

constraint_columns = ["SEX",
                      "MARSTAT",
                      "AGECLASS",
                      "HATLEVEL"]
                      # "MAINSTAT",
                      # "NATUREOFOCCUPANCY"]

sexes = [None, "M", "F"]
# micro_ages = sorted(list(micro_df["AGECLASS"].unique()))

households = {}
household_counter = 0
for (quarter, household), group in tqdm(grouped):
    if quarter == quarter_to_study:
        households[household] = {}
        for idx, individual in group.iterrows():
            # households[household][idx] = {}
            households[household][idx] = []

            individuals_sex_as_letter = sexes[individual["SEX"]]

            # Age
            # translated_age = saps_ages[str(individual["AGECLASS"]) if not isinstance(individual["AGECLASS"], str) else individual["AGECLASS"]]
            translated_age = saps_ages[individual["AGECLASS"]]
            # households[household][idx][translated_age + individuals_sex_as_letter] = True
            # households[household][idx]["T1_1"] = translated_age + individuals_sex_as_letter
            households[household][idx].append(translated_age + individuals_sex_as_letter)

            # Marital Status
            # households[household][idx][saps_marital_statuses[individual["MARSTAT"]] + individuals_sex_as_letter] = True
            households[household][idx].append(saps_marital_statuses[individual["MARSTAT"]] + individuals_sex_as_letter)
            # households[household][idx]["T1_2"] = saps_marital_statuses[individual["MARSTAT"]] + individuals_sex_as_letter

            # Nature of Occupancy
            # if individual["NATUREOFOCCUPANCY"]:
            #     households[household][idx][] = True
            # else:
            #     households[household][idx]["T6_3_NSP"] = True

            # Level of Education Completed
            level_of_education = individual["HATLEVEL"]
            # try:
            #     households[household][idx]["T10_4"] = saps_levels_of_education[level_of_education] + individuals_sex_as_letter
            # except KeyError:  # HATLEVEL empty
            #     households[household][idx]["T10_4"] = "T10_4_NS" + individuals_sex_as_letter
            try:
                households[household][idx].append(saps_levels_of_education[level_of_education] + individuals_sex_as_letter)
            except KeyError:  # HATLEVEL empty
                households[household][idx].append("T10_4_NS" + individuals_sex_as_letter)

            # Household size
            if num_people_in_each_household[household] >= 8:
                # households[household][idx]["T5_2"] = f"T5_2_GE8PP"
                households[household][idx].append(f"T5_2_GE8PP")
            else:
                # households[household][idx]["T5_2"] = f"T5_2_{num_people_in_each_household[household]}PP"
                households[household][idx].append(f"T5_2_{num_people_in_each_household[household]}PP")

            # households[household][idx]["others"] = {}
            #
            # for characteristic in micro_columns:
            #     if characteristic not in ["refperiod", "QHHNUM"]:
            #         if characteristic not in constraint_columns:
            #             # households[household][idx][characteristic] = individual[characteristic]
            #             households[household][idx]["others"][characteristic] = individual[characteristic]
                    # else:
                    #     if characteristic == "SEX":
                    #         # 1 = Male, 2 = Female
                    #
                    #         households[household][idx][sexes[individuals_sex_as_number]] = True
                    #     elif characteristic == "MARSTAT":
                    #         marital_status = individual[characteristic]
                    #         if marital_status == 1:
                    #             households[household][idx]["T1_2SGL"] = True

with open("2023q3_households_new_schema_more_constraints_no_excess.pkl", "wb") as f:
    pickle.dump(households, f)

print(1)

# age_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$"
# regex_match_string = re.compile(age_regex)
# columns = sorted(list(filter(regex_match_string.match, sap_df.columns)))
#
# age_class_conversion = {age:  for idx, age in enumerate(sorted(micro_df["AGECLASS"]))}