import pickle as pkl
from os import listdir
import pandas as pd
from tqdm import tqdm

results_folder = "./results/ipf/"

eds = [f.split(".")[0] for f in listdir(results_folder)]

for ed in tqdm(eds):
    ed_df = pd.read_csv(results_folder + ed + ".csv")
    this_eds_pop = []
    for idx, row in ed_df.iterrows():
        persons_age = row["Var1"]
        persons_marital_status = row["Var2"]
        persons_house_size = row["Var3"]
        persons_employment = row["Var4"]
        persons_education = row["Var5"]

        this_eds_pop.append([persons_age,
                             persons_marital_status,
                             persons_house_size,
                             persons_employment,
                             persons_education])

    with open(results_folder + ed + ".pkl", "wb") as f:
        pkl.dump(this_eds_pop, f)

print("Done")
