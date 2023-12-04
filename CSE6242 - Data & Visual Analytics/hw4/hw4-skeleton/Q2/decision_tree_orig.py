from util import entropy, information_gain, partition_classes
import numpy as np 
import ast


class DecisionTree(object):
    def __init__(self, depth=1, max_depth=3):
        # Initializing the tree as an empty dictionary or list, as preferred
        self.tree = {}
        self.depth = depth
        self.max_depth = max_depth

    def learn(self, X, y):
        # TODO: Train the decision tree (self.tree) using the the sample X and labels y
        # You will have to make use of the functions in utils.py to train the tree

        # One possible way of implementing the tree:
        #    Each node in self.tree could be in the form of a dictionary:
        #       https://docs.python.org/2/library/stdtypes.html#mapping-types-dict
        #    For example, a non-leaf node with two children can have a 'left' key and  a 
        #    'right' key. You can add more keys which might help in classification
        #    (eg. split attribute and split value)
        if len(y) == 0:
            self.tree['label'] = 'fail'
            return
        nx = np.array(X)
        (max_row, max_col) = nx.shape

        if self.depth <= self.max_depth:
            (vals, counts) = np.unique(y, return_counts=True) 
            idx = np.argmax(counts)
            if self.depth == self.max_depth or len(counts) == 1:
                self.tree['label'] = 'leaf'
                self.tree['value'] = vals[idx]
                return

            max_gain = 0
            for i in range(max_col):
                # print("processing X[%s]" % i)
                uniq_x = np.quantile(nx[:, i], [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9])
                for item in uniq_x:
                    # print("partitioning classes X[%s]: %s" % (i, item))
                    (X_left, X_right, y_left, y_right) = partition_classes(X, y, i, item)
                    # print('calculating gain...')
                    gain = information_gain(y, [y_left, y_right])
                    if (gain > max_gain):
                        # print('found new max gain: %s' % gain)
                        max_gain = gain
                        attr_idx = i
                        attr_value = item
                        X1 = X_left
                        y1 = y_left
                        X2 = X_right
                        y2 = y_right

            subtree1 = DecisionTree(depth=self.depth + 1)
            subtree2 = DecisionTree(depth=self.depth + 1)
            subtree1.learn(X1, y1)
            subtree2.learn(X2, y2)
            self.tree['label'] = 'normal'
            self.tree['attr'] = attr_idx
            self.tree['split'] = attr_value
            self.tree['left'] = subtree1
            self.tree['right'] = subtree2
        else:
            self.tree['label'] = 'fail'
        
    def classify(self, record):
        # TODO: classify the record using self.tree and return the predicted label
        if self.tree['label'] == "fail":
            return 0
        elif self.tree['label'] == "leaf":
            return self.tree['value']
        elif record[self.tree['attr']] <= self.tree['split']:
            return self.tree['left'].classify(record)
        else:
            return self.tree['right'].classify(record)