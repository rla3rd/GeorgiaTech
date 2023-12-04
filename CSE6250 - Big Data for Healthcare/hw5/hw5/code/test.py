from mydatasets import visit_collate_fn
import numpy as np

p1 = np.array([1, 1, 0, 0, 0, 0])
p2 = np.array([[0, 0, 0, 1, 0, 0], [1, 0, 1, 0, 0, 0], [0, 1, 0, 0, 1, 0]])
p3 = np.array([[0, 1, 0, 0, 0, 0], [0, 0, 0, 0, 0, 1]])
batch = [(p1, 1), (p2, 0), (p3, 1)]
result = visit_collate_fn(batch)
print(result)