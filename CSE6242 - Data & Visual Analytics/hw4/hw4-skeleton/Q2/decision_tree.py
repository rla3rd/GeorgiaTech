from util import entropy, information_gain, partition_classes
import numpy as np 
import ast


class DecisionTree(object):
    def __init__(self):
        # Initializing the tree as an empty dictionary or list, as preferred
        self.tree = {}
        self.max_depth = 3

    def learn(self, X, y):
        # TODO: Train the decision tree (self.tree) using the the sample X and labels y
        # You will have to make use of the functions in utils.py to train the tree

        # One possible way of implementing the tree:
        #    Each node in self.tree could be in the form of a dictionary:
        #       https://docs.python.org/2/library/stdtypes.html#mapping-types-dict
        #    For example, a non-leaf node with two children can have a 'left' key and  a 
        #    'right' key. You can add more keys which might help in classification
        #    (eg. split attribute and split value)
        self.tree = self.build_tree(X, y, 1)

    def build_tree(self, X, y, depth):
        nx = np.array(X)
        (max_row, max_col) = nx.shape
        tree = {}
        
        if depth <= self.max_depth:
            # or len(counts) == 1:
            (vals, counts) = np.unique(y, return_counts=True) 
            idx = np.argmax(counts)
            if depth == self.max_depth or len(counts) == 1:
                tree['label'] = 'leaf'
                tree['value'] = vals[idx]
                return tree

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
            
            tree['label'] = 'normal'
            tree['attr'] = attr_idx
            tree['split'] = attr_value
            left = self.build_tree(X1, y1, depth + 1)
            tree['left'] = left
            right = self.build_tree(X2, y2, depth + 1)
            tree['right'] = right
            return tree


    def classify(self, record):
        # TODO: classify the record using self.tree and return the predicted label
        node = self.tree
        while node['label'] == 'normal':
            if record[node['attr']] <= node['split']:
                node = node['left']
            else:
                node = node['right']
        
        return node['value']
        