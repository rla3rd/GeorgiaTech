import numpy as np


class RTLearner(object):
    def __init__(self, leaf_size=1, verbose=False):
        self.leaf_size = leaf_size
        self.verbose = verbose
        self.tree = None

    def author(self):
        return "ralbright7"

    def add_evidence(self, data_x, data_y):
        self.tree = self.build_tree(data_x, data_y)

    def build_tree(self, data_x, data_y):
        (max_row, max_col) = data_x.shape
        size = data_y.shape[0]
        (vals, counts) = np.unique(data_y, return_counts=True)

        if size <= self.leaf_size or len(counts) == 1:
            return np.array([["leaf", np.mean(data_y), None, None]])

        feature_idx = np.random.randint(0, max_col)
        column = data_x[:, feature_idx]
        split_value = np.median(column)
        idx = column <= split_value
        if np.alltrue(idx) or np.alltrue(~idx):
            return np.array([["leaf", np.mean(data_y), None, None]])

        x_left = data_x[idx]
        x_right = data_x[~idx]
        y_left = data_y[idx]
        y_right = data_y[~idx]

        left = self.build_tree(x_left, y_left)
        right = self.build_tree(x_right, y_right)
        root = np.array([[feature_idx, split_value, 1, left.shape[0]+1]])
        tree = np.vstack((root, left, right))
        return tree

    def query(self, points):
        (max_row, max_col) = points.shape
        predictions = np.empty(max_row)
        for i in np.arange(max_row):
            point = points[i]
            row = 0
            node = self.tree[row]
            while node[0] != "leaf":
                feature_idx = int(node[0])
                split_value = node[1]
                if point[feature_idx] <= split_value:
                    row += int(node[2])
                    node = self.tree[row]
                else:
                    row += int(node[3])
                    node = self.tree[row]
            predictions[i] = node[1]
        return predictions


if __name__ == "__main__":
    print("this is the RT Learner")
