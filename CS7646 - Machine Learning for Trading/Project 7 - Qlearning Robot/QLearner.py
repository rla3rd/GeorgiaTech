""""""  		  	   		   	 		  		  		    	 		 		   		 		  
"""  		  	   		   	 		  		  		    	 		 		   		 		  
Template for implementing QLearner  (c) 2015 Tucker Balch  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
Copyright 2018, Georgia Institute of Technology (Georgia Tech)  		  	   		   	 		  		  		    	 		 		   		 		  
Atlanta, Georgia 30332  		  	   		   	 		  		  		    	 		 		   		 		  
All Rights Reserved  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
Template code for CS 4646/7646  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
Georgia Tech asserts copyright ownership of this template and all derivative  		  	   		   	 		  		  		    	 		 		   		 		  
works, including solutions to the projects assigned in this course. Students  		  	   		   	 		  		  		    	 		 		   		 		  
and other users of this template code are advised not to share it with others  		  	   		   	 		  		  		    	 		 		   		 		  
or to make it available on publicly viewable websites including repositories  		  	   		   	 		  		  		    	 		 		   		 		  
such as github and gitlab.  This copyright statement should not be removed  		  	   		   	 		  		  		    	 		 		   		 		  
or edited.  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
We do grant permission to share solutions privately with non-students such  		  	   		   	 		  		  		    	 		 		   		 		  
as potential employers. However, sharing with other current or future  		  	   		   	 		  		  		    	 		 		   		 		  
students of CS 7646 is prohibited and subject to being investigated as a  		  	   		   	 		  		  		    	 		 		   		 		  
GT honor code violation.  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
-----do not edit anything above this line---  		  	   		   	 		  		  		    	 		 		   		 		  

Student Name: Richard Albright (replace with your name)
GT User ID: ralbright7 (replace with your User ID)
GT ID: 903548616 (replace with your GT ID)
"""
import random as rand
import numpy as np


class QLearner(object):
    """
    This is a Q learner object.

    :param num_states: The number of states to consider.
    :type num_states: int
    :param num_actions: The number of actions available..
    :type num_actions: int
    :param alpha: The learning rate used in the update rule. Should range
        between 0.0 and 1.0 with 0.2 as a typical value.
    :type alpha: float
    :param gamma: The discount rate used in the update rule. Should range
        between 0.0 and 1.0 with 0.9 as a typical value.
    :type gamma: float
    :param rar: Random action rate: the probability of selecting a random
        action at each step. Should range between 0.0 (no random actions)
        to 1.0 (always random action) with 0.5 as a typical value.
    :type rar: float
    :param radr: Random action decay rate, after each update, rar = rar * radr.
        Ranges between 0.0 (immediate decay to 0) and 1.0 (no decay).
        Typically 0.99.
    :type radr: float
    :param dyna: The number of dyna updates for each regular update.
        When Dyna is used, 200 is a typical value.
    :type dyna: int
    :param verbose: If “verbose” is True, your code can print out
        information for debugging.
    :type verbose: bool
    """
    def __init__(
        self,
        num_states=100,
        num_actions=4,
        alpha=0.2,
        gamma=0.9,
        rar=0.5,
        radr=0.99,
        dyna=0,
        verbose=False
    ):
        """
        Constructor method
        """
        self.num_states = num_states
        self.num_actions = num_actions
        self.alpha = alpha
        self.gamma = gamma
        self.rar = rar
        self.radr = radr
        self.dyna = dyna
        self.verbose = verbose

        self.s = 0
        self.a = 0
        self.Q = np.zeros((self.num_states, self.num_actions))
        self.replay = []
        if self.dyna > 0:
            self.Tc = np.ones((
                self.num_states,
                self.num_actions,
                self.num_states))/100000

            self.calc_T()

    def author(self):
        return 'ralbright7'

    def calc_T(self):
        self.T = self.Tc/np.sum(self.Tc, axis=2, keepdims=True)

    def update_Q(self, alpha, gamma, s, a, r, sprime, action):
        self.Q[s, a] = (
            (1 - alpha) * self.Q[s, a]
            + alpha * (r + gamma * np.max(self.Q[sprime, action])))

    def querysetstate(self, s):
        """
        Update the state without updating the Q-table

        :param s: The new state
        :type s: int
        :return: The selected action
        :rtype: int
        """
        # decide to use our new state or random action
        self.s = s
        if rand.random() < self.rar:
            action = rand.randint(0, self.num_actions - 1)
        else:
            action = np.argmax(self.Q[s])
        if self.verbose:
            print(f"s = {s}, a = {action}")
        return action

    def query(self, s_prime, r):
        """
        Update the Q table and return an action

        :param s_prime: The new state
        :type s_prime: int
        :param r: The immediate reward
        :type r: float
        :return: The selected action
        :rtype: int
        """
        # use self.a in here somewhere
        # rar * radr too
        # if action < rar, take random action
        a = self.a
        s = self.s
        alpha = self.alpha
        gamma = self.gamma

        # update the Q table
        action = np.argmax(self.Q[s])
        self.update_Q(alpha, gamma, s, a, r, s_prime, action)
        self.replay.append((s, a, r, s_prime))

        # if dyna > 0 then hallucinate
        if self.dyna > 0:

            self.Tc[s, a, s_prime] += 1
            self.calc_T()
            # hallucinate through dyna range
            for _ in range(self.dyna):
                ds, da, dr, dsp = self.replay[
                    np.random.choice(len(self.replay))]
                dap = np.argmax(self.Q[dsp])
                self.update_Q(alpha, gamma, ds, da, dr, dsp, dap)

        # decide to use our new state or random action
        if rand.random() < self.rar:
            action = rand.randint(0, self.num_actions - 1)
        else:
            action = np.argmax(self.Q[s_prime])

        # update the last state, action, and random action rate
        self.s = s_prime
        self.a = action
        self.rar = self.rar * self.radr

        if self.verbose:
            print(f"s = {s_prime}, a = {action}, r={r}")
        return action


if __name__ == "__main__":
    print("Remember Q from Star Trek? Well, this isn't him")
