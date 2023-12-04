import numpy as np


class BagLearner(object):
    def __init__(
        self,
        learner,
        kwargs={},
        bags=20,
        boost=False,
        verbose=False
    ):
        self.learner = learner
        self.kwargs = kwargs
        self.bags = bags
        self.boost = boost
        self.verbose = verbose
        self.learners = [self.learner(**kwargs) for i in np.arange(self.bags)]

    def author(self):
        return "ralbright7"

    def add_evidence(self, data_x, data_y):
        size = data_y.shape[0]
        for lrn in self.learners:
            idx = np.random.choice(size, size, replace=True)
            sample_x = data_x[idx]
            sample_y = data_y[idx]
            lrn.add_evidence(sample_x, sample_y)

    def query(self, points):
        # (max_row, max_col) = points.shape
        predictions = np.empty(self.bags, dtype=object)
        i = 0
        for l in np.arange(self.bags):
            pred = self.learners[l].query(points)
            predictions[i] = pred
            i += 1

        predictions = np.mean(predictions, axis=0)
        return predictions


if __name__ == "__main__":
    print("this is the Bag Learner")
