from constants import tables_and_characteristics_with_blanks, \
    saps_levels_of_education, \
    saps_employment_statuses, \
    sexes
from math import isnan


def household_size(qhhnum, qhhnum_counts):
    size = qhhnum_counts.get(qhhnum)
    if size < 8:
        return "T5_2_" + str(size) + "PP"
    else:
        return "T5_2_GE8PP"


def employment_status(row):
    if isnan(row["MAINSTAT"]) or (row["MAINSTAT"] == ""):
        return "T8_1_OTH" + sexes[row["SEX"]]
    elif row["MAINSTAT"] == 9:
        return "T8_1_NA"
    else:
        return saps_employment_statuses[row["MAINSTAT"]] + sexes[row["SEX"]]


def highest_level_of_education(row):
    childrens_ages = ["T1_1AGE0_4M",
                      "T1_1AGE5_9M",
                      "T1_1AGE10_14M",
                      "T1_1AGE0_4F",
                      "T1_1AGE5_9F",
                      "T1_1AGE10_14F"]
    if row["HATLEVEL"]==999:
        return "T10_4_NA"
    elif (row["T1_1"] in childrens_ages) or ("T8_1_S" in row["T8_1"]):
        return "T10_4_NA"
    elif isnan(row["HATLEVEL"]) or (row["HATLEVEL"] == ""):
        return "T10_4_NS" + sexes[row["SEX"]]
    else:
        return saps_levels_of_education[row["HATLEVEL"]] + sexes[row["SEX"]]
