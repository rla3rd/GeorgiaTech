import numpy as np
import BagLearner, LinRegLearner
class InsaneLearner(object):
    def __init__(self, verbose=False):
        self.learners = [BagLearner.BagLearner(LinRegLearner.LinRegLearner) for i in np.arange(20)]
    def author(self): return "ralbright7"
    def add_evidence(self, data_x, data_y):
        [lrn.add_evidence(data_x, data_y) for lrn in self.learners]
    def query(self, points):
        predictions = np.empty(20, dtype=object)
        i = 0
        for l in np.arange(20):
            predictions[i] = self.learners[l].query(points)
            i += 1
        predictions = np.mean(predictions, axis=0)
        return predictions
