import random
from math import ceil
import numpy as np
from scipy.stats import chi2


def dupe_dict(dict_to_dupe: dict, size_required: int):
    num_dupes_needed = ceil(size_required / len(dict_to_dupe))

    new_dict = dict_to_dupe.copy()
    for _ in range(1, num_dupes_needed):
        for _, value in dict_to_dupe.items():
            while True:
                new_key = random.randint(1, len(dict_to_dupe) * num_dupes_needed * 5)
                if (new_key not in dict_to_dupe) and (new_key not in new_dict):
                    new_dict[new_key] = value
                    break

    return new_dict


def voas_pearson_chi(observed: list, expected: list):
    # Adapted from GenSynthPop
    # https://github.com/A-Practical-Agent-Programming-Language/GenSynthPop-Python
    alpha = 0.05

    degrees_of_freedom = len(observed)
    critical_value = chi2.ppf(1 - alpha, df=degrees_of_freedom)

    enumerator = np.square([o - e for o, e in zip(observed, expected)])
    denominator = [d if d != 0 else 1 for d in expected]
    ratios = [e / denominator[i] for i, e in enumerate(enumerator)]
    p_value = 1 - chi2.cdf(sum(ratios), df=degrees_of_freedom)
    return sum(ratios), p_value, degrees_of_freedom, critical_value


def voas_z_squared(observed: list, expected: list, observed_proportions: list, expected_proportions: list):
    # Adapted from GenSynthPop
    # https://github.com/A-Practical-Agent-Programming-Language/GenSynthPop-Python
    alpha = 0.05

    exp_total = sum(expected)

    enumerators = [o - e for o, e in zip(observed_proportions, expected_proportions)]
    denominators = []
    zs = []
    for i, expected_proportion in enumerate(expected_proportions):
        if expected_proportion != 0:
            continuity_correction_factor = (1 / (2 * exp_total))
            if enumerators[i] >= 0:
                enumerators[i] -= continuity_correction_factor
            else:
                enumerators[i] += continuity_correction_factor

        if expected_proportion == 0:
            expected_proportion = 1 / exp_total

        denominators.append(np.sqrt(expected_proportion * (1 - expected_proportion) / exp_total))

        zs.append(enumerators[i] / denominators[i])

    degrees_of_freedom = len(observed)
    z_squared = sum(z*z for z in zs)
    p_value = 1 - chi2.cdf(z_squared, df=degrees_of_freedom)
    critical_value = chi2.ppf(1 - alpha, df=degrees_of_freedom)

    return z_squared, p_value, degrees_of_freedom, critical_value


def voas_sae(observed: list, expected: list):
    return sum([abs(o - e) for o, e in zip(observed, expected)]) / sum(expected)


if __name__ == '__main__':
    count_x=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    count_y=[1.1, 1.9, 3.1, 3.9, 5.1, 5.9, 7.1, 7.9, 9.1, 9.9]

    print(voas_pearson_chi(count_x, count_y))