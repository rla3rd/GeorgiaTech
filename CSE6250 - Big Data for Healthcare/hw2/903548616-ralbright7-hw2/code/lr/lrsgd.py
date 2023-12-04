# Do not use anything outside of the standard distribution of python
# when implementing this class
import math


class LogisticRegressionSGD:
    """
    Logistic regression with stochastic gradient descent
    """

    def __init__(self, eta, mu, n_feature):
        """
        Initialization of model parameters
        """
        self.eta = eta
        self.weight = [0.0] * n_feature
        self.mu = mu

    def fit(self, X, y):
        """
        Update model using a pair of training sample
        """
        gamma = math.fsum(
            (self.weight[feature] * value for feature, value in X))
        if gamma < 0:
            sigma = -1.0 * (1.0 - 1.0/(1.0 + math.exp(gamma)))
        else:
            sigma = -1.0 * 1.0 / (1.0 + math.exp(-gamma))

        for feature, value in X:
            self.weight[feature] = \
                self.weight[feature] + self.eta * (value * sigma + y)

        for index, _ in enumerate(self.weight):
            self.weight[index] = \
                self.weight[index] - \
                2 * self.eta * self.mu * self.weight[index]

    def predict(self, X):
        """
        Predict 0 or 1 given X and the current weights in the model
        """
        return 1 if self.predict_prob(X) > 0.5 else 0

    def predict_prob(self, X):
        """
        Sigmoid function
        """
        return 1.0 / (1.0 + math.exp(
            -math.fsum((self.weight[f]*v for f, v in X))))
