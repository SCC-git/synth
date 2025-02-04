# Synthetic Population Generation for Ireland

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.14802378.svg)](https://doi.org/10.5281/zenodo.14802378)

Synthetic populations created with IPF and conditional probabilities are given in the [results folder](results/).

To create your own populations, follow these steps:
1. Clone this repository to a folder of your choice.
2. Apply for the [Labour Force Survey (LFS) microdata](https://www.ucd.ie/issda/data/lfs/) from the ISSDA. Once access is granted, add the LFS folder to the same folder as this repository.
3. Download the [Small Area Population Statistics (SAPS) data](https://www.cso.ie/en/media/csoie/census/census2022/SAPS_2022_CSOED3270923.csv) from the CSO website. Place it in the same folder as this repository.
4. Pre-process and normalise the SAPS data by running [csv_constraint_loader](csv_constraint_loader.py) or just use the [given pre-processed data](rescaled_ed_aggregates_ordered.csv).
5. The next steps depend on the approach desired:
### Synthetic Reconstruction
#### Conditional Probabilities 
[This file](conditional_probabilities.py) is ready to run immediately and will place the resulting populations in the results/conditional_probabilities folder.

#### IPF
1. Run the [IPF Initial Matrix file](ipf_initial_matrix.py). This will create the crosstabulation of characteristics in the LFS microdata which is needed for IPF and save it to lfs_crosstab.npy.
2. Run [ipf.R](ipf.R). This uses mipfp to create the populations and saves them to CSVs in the [results/ipf folder](results/ipf).
3. Run [ipf_results_to_pkl.py](ipf_results_to_pkl.py) to put the IPF results in the same format as the other approaches' results (a list of each person's characteristics)

### Combinatorial Optimisation
#### Simulated Annealing
Run [generate_population_households](generate_population_households.py) with the argument simulated_annealing. The resulting populations will be placed in the results/simulated_annealing folder.

#### Genetic Algorithms
Run [generate_population_households](generate_population_households.py) with the argument genetic_algorithms. The resulting populations will be placed in the results/ga folder.

## Loading the generated populations
To load the generated population, simply use ```pickle.load(ed_filename)``` with the relevant ED's file. 

For the Synthetic Reconstruction approaches, the result will be a list of lists representing a population of people described as a list of characteristics. 

For the Combinatorial Optimisation approaches, the result will be a dictionary of dictionaries of lists representing a population of households of people (with IDs from the LFS) described as a list of characteristics. 
Having access to each person's ID means that non-constrained variables from the LFS, such as income, can be included. 


These populations can then be used for ABM/microsimulation/etc.

