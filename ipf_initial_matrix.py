from collections import Counter
import numpy as np
import pandas as pd
from constants import saps_marital_statuses, \
    saps_ages, \
    sexes
from lfs_status_converters import household_size, employment_status, highest_level_of_education

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
micro_df = micro_df[["T1_1", "T1_2", "T5_2", "T8_1", "T10_"]]

columns_of_interest = ["T1_1", "T1_2", "T5_2", "T8_1", "T10_"]
crosstab = pd.crosstab(micro_df[columns_of_interest[0]], [micro_df[c] for c in columns_of_interest[1:]], dropna=False)
np_crosstab = crosstab.to_numpy()
np_crosstab_reshaped = np.reshape(np_crosstab, ([len(micro_df[column].unique()) for column in columns_of_interest]))

numpy_array_filename = "lfs_crosstab.npy"
with open(numpy_array_filename, "wb") as f:
    np.save(f, np_crosstab_reshaped)

print(np_crosstab_reshaped)
