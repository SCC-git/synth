import random
import numpy as np


def calculate_error(error_households):
    # return - sum(error_households)
    return error_households[0]**2.0 + error_households[1]**2.0


def tournament_selection(full_population, fitnesses, tournament_size):
    # Machine learning mastery way
    # first random selection
    best_idx = np.random.randint(len(full_population))
    for pop_idx in np.random.randint(0, len(full_population), tournament_size-1):
        # check if better
        if fitnesses[pop_idx] < fitnesses[best_idx]:
            best_idx = pop_idx

    return full_population[best_idx]


# decode bitstring to numbers
def decode(bounds, n_bits, bitstring):
    decoded = list()
    largest = 2**n_bits
    for i in range(len(bounds)):
        # extract the substring
        start, end = i * n_bits, (i * n_bits)+n_bits
        substring = bitstring[start:end]
        # convert bitstring to a string of chars
        chars = ''.join([str(s) for s in substring])
        # convert string to integer
        integer = int(chars, 2)
        # scale integer to desired range
        value = bounds[i][0] + (integer/largest) * (bounds[i][1] - bounds[i][0])
        # store
        decoded.append(value)
    return decoded


# Crossover
def crossover(parent_one, parent_two, uniform_rate):
    indexes_to_crossover = [i for i in range(len(parent_one)) if random.uniform(0, 1) < uniform_rate]

    child_one = [parent_two[i] if (i in indexes_to_crossover) else parent_one[i] for i in range(len(parent_one))]
    child_two = [parent_one[i] if (i in indexes_to_crossover) else parent_two[i] for i in range(len(parent_one))]

    return [child_one, child_two]


# Mutation
def mutate(individual, mutation_rate):
    # num_households_to_mutate = round(np.random.normal(loc=mutation_rate * size_of_ed, scale=5.75))
    indexes_to_mutate = [i for i in range(len(individual)) if random.uniform(0, 1) < mutation_rate]
    if len(indexes_to_mutate) > 0:
        # indexes_to_mutate = random.sample(range(len(individual)), num_households_to_mutate)
        mutated_individual = []
        for i in range(len(individual)):
            if i not in indexes_to_mutate:
                mutated_individual.append(individual[i])
            else:
                # Put in a different household instead of the old one
                mutated_individual.append(1 - individual[i])
    else:
        mutated_individual = individual
    return mutated_individual


def genetic_algorithm(population_size: int=50):
    # eds = ["167065"] # Navan Rural
    # eds = ["68003"] # Barna
    # eds = ["68013"] # Newcastle
    # eds = ed_aggregates["ED_ID"].unique()

    uniform_rate = 0.9
    # mutation_rate = 0.05

    tournament_size = 10
    bounds = [[-5.0, 5.0], [-5.0, 5.0]]
    num_bits = 16
    # num_bits = 20
    mutation_rate = 1.0 / (float(num_bits) * len(bounds))
    # mutation_rate = 0.05
    # elitism = True

    num_generations = 100

    # Initialise population with random individuals (lists of households)
    # population = [np.random.randint(0, 2, num_bits).tolist() for _ in range(population_size)]
    population = [np.random.randint(0, 2, num_bits * len(bounds)).tolist() for _ in range(population_size)]
    best, best_eval = 0, calculate_error(decode(bounds, num_bits, population[0]))

    for generation in range(num_generations):
        # print(f"Generation: {generation}")
        decoded = [decode(bounds, num_bits, pop) for pop in population]
        # fitnesses = [calculate_error(p) for p in population]
        fitnesses = [calculate_error(d) for d in decoded]
        for i in range(population_size):
            if fitnesses[i] < best_eval:
                best, best_eval = population[i], fitnesses[i]
                print(f">{generation}, new best ({decoded[i]}) = {fitnesses[i]}")

        parents = [tournament_selection(population, fitnesses, tournament_size) for _ in range(population_size)]
        new_population = []
        for i in range(0, population_size, 2):
            # print("SELECTION\n")
            # first_parent = tournament_selection(population, fitnesses, tournament_size)
            # second_parent = tournament_selection(population, fitnesses, tournament_size)
            p1 = parents[i]
            p2 = parents[i]

            # print("CROSSOVER\n")
            children = crossover(p1, p2, uniform_rate)

            for child in children:
                # Mutate
                new_population.append(mutate(child, mutation_rate))
            # new_individual = mutate(new_individual)
            # new_population.extend(mutated_new_individuals)

        population = new_population

        # our_error_characteristic_counts = defaultdict(int)
        # for fittest_household in fittest_population:
        #     for _, fittest_individual in fittest_household.items():
        #         # for table, value in fittest_individual.items():
        #         for characteristic in fittest_individual:
        #             our_error_characteristic_counts[characteristic] += 1
                    # Value is not blank in SAPS data
                    # if (table != "others") and ("T" in value):
                    #     our_error_characteristic_counts[value] += 1
        # print("Characteristic counts: Ours | Theirs")
        # for characteristic, count in our_error_characteristic_counts.items():
        #     if "T" in characteristic:
        #         print(f"\t{characteristic}: {count} | {this_eds_aggregates[characteristic]}")

        # print("\nHouseholds:")
        # for idx, household in enumerate(best_solution):
        #     print(f"Household {idx}")
        #     for individuals_id, individual in household.items():
        #         print(f"\tIndividual {individuals_id}")
        #         for error_column in individual.keys():
        #             if error_column != "others":
        #                 print(f"\t\t{individual[error_column]}")
        #     print("\n")


if __name__ == '__main__':
    # ed_totals = pd.read_csv("SAPS_2022_CSOED3270923.csv", encoding="latin-1")
    # ed_totals = pd.read_csv("SAPS_2022_CSOED3270923_combined_qualis.csv", encoding="latin-1")
    # with open('2023q3_households_new_schema_more_constraints.pkl', 'rb') as f:
    # with open('2023q3_households_new_schema_more_constraints_no_excess.pkl', 'rb') as f:
    #     q3_households = pkl.load(f)

    # print(f"Num. households: {len(q3_households)}")
    #
    # error_regex = r"(^T1_1).+(?<!T)(?<!TM)(?<!TF)$|" \
    #               r"(^T1_2).+(?<!T)(?<!DIVM)(?<!SEPM)(?<!TM)(?<!TF)(?<!DIVF)(?<!SEPF)$|" \
    #               r"(^T10_4).+(?<!T)(?<!TM)(?<!TF)$|" \
    #               r"(^T5_2_)[^T].*P$"
    # regex_match_string = re.compile(error_regex)
    # error_columns = sorted(list(filter(regex_match_string.match, ed_totals.columns)))

    # lp = LineProfiler()
    # lp.add_function(tournament_selection)
    # lp.add_function(calculate_error)
    # lp_wrapper = lp(genetic_algorithm)
    # lp_wrapper(q3_households, ed_totals, error_columns, 50)
    # lp.print_stats()
    genetic_algorithm(population_size=50)
