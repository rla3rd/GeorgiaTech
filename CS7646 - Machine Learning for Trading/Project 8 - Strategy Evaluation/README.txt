ManualStrategy.py

This file executes the Manual Rules Based Strategy in the report.

StrategyLearner.py 

This file generates the Q-Learning Strategy in the report

QLearner.py

This file contains the Q-Learner object that is used in the StrategyLearner.py file.
This file is not run on its own.

indicators.py

This file contains the indicators used in both the ManualStrategy.py and StrategyLearner.py files.
This file is not run on its own.

marketsimcode.py

This file includes a modified market simulator that takes a trades dataframe as input
This file is not run on its own.

experiment1.py

This file runs experiment 1, which compares the Q-Learner to the Manual Strategy and the Benchmark.
It is run on the in-sample time period and includes commissions and impact.

experiment2.py

This file runs experiment 2, which compares the Q-Learner to the Manual Strategy and the Benchmark.
It is run on the in-sample time period and does not include commissions and impact.

testproject.py

This file calls the necessary function calls from ManualStrategy.py,
StrategyLearner.py, experiment1.py, and experiment2.py to generate all the charts 
and data needed for the report.

execution of testproject.py
PYTHONPATH=../:. python testproject.py
