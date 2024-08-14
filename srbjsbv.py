import random
from collections import Counter
from tqdm import tqdm
import numpy as np

results = []
for _ in tqdm(range(100_000)):
    num_swaps = 0
    for _ in range(70):  # 700 households
        if random.uniform(0, 1) < 0.05:  # 0.7 chance of crossover
            num_swaps += 1
    results.append(num_swaps)

counter = Counter(results)
sorted_keys = sorted(list(counter.keys()))
for key in sorted_keys:
    print(f"{key}: {counter[key]}")

print(f"\nMean: {np.mean(results)}")
print(f"Std. dev.: {np.std(results)}")