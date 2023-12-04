""""""  		  	   		   	 		  		  		    	 		 		   		 		  
"""  		  	   		   	 		  		  		    	 		 		   		 		  
Test a learner.  (c) 2015 Tucker Balch  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
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
"""  		  	   		   	 		  		  		    	 		 		   		 		  

import math
import sys

import numpy as np
import time

import LinRegLearner as lrl
import DTLearner as dtl
import RTLearner as rtl
import BagLearner as bgl
from matplotlib import pyplot as plt

np.seterr(invalid='ignore')

def isfloat(s):
    try:
        float(s)
        return True
    except Exception:
        return False

# taken from https://stackoverflow.com/questions/893657/how-do-i-calculate-r-squared-using-python-and-numpy
def r_squared(x, y):
    zx = (x - np.mean(x)) / np.std(x, ddof=1)
    zy = (y - np.mean(y)) / np.std(y, ddof=1)
    r = np.sum(zx * zy) / (len(x) - 1)
    return r ** 2


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python testlearner.py <filename>")
        sys.exit(1)
    inf = open(sys.argv[1])
    data = np.array(
        [np.array(l) for l in [
            list(map(float, [
                i for i
                in s.strip().split(",")
                if isfloat(i)])) for s in inf.readlines()
                ] if l != []])
    row_length = len(data[0])
    data = np.concatenate(data).reshape(data.shape[0], row_length)

    # compute how much of the data is training and testing
    train_rows = int(0.6 * data.shape[0])
    test_rows = data.shape[0] - train_rows

    # separate out training and testing data
    train_x = data[:train_rows, 0:-1]
    train_y = data[:train_rows, -1]
    test_x = data[train_rows:, 0:-1]
    test_y = data[train_rows:, -1]

    print(f"{test_x.shape}")
    print(f"{test_y.shape}")

    leaf_size = np.arange(50) + 1
    
    # Experiment 1
    insample_rmse = []
    outsample_rmse = []
    dt_train_time = []
    for i in leaf_size:
        dt = dtl.DTLearner(leaf_size=i, verbose=True)
        st = time.time()
        dt.add_evidence(train_x, train_y)  # train it
        et = time.time()
        dt_train_time.append(et - st)

        # evaluate in sample
        pred_y = dt.query(train_x)  # get the predictions
        rmse = math.sqrt(((train_y - pred_y) ** 2).sum() / train_y.shape[0])
        insample_rmse.append(rmse)

        # evaluate out of sample
        pred_y = dt.query(test_x)  # get the predictions
        rmse = math.sqrt(((test_y - pred_y) ** 2).sum() / test_y.shape[0])
        outsample_rmse.append(rmse)

    file = open('p3_results.txt', 'w')
    file.write('Experiment 1: DTLearner\n')
    file.write("\n")
    file.write('leaf_size,dt_insample_rmse,dt_outsample_rmse\n')
    for i in leaf_size:
        file.write(f"{i},{insample_rmse[i-1]},{outsample_rmse[i-1]}\n")
    file.write("\n")
    file.write("\n")

    plt.title("Experiment 1 DTLearner: Leaf Size vs RMSE")
    ins = plt.plot(leaf_size, insample_rmse, color='orange')
    ins[0].set_label('in sample')
    out = plt.plot(leaf_size, outsample_rmse, color='blue')
    out[0].set_label('out of sample')
    plt.xlabel("Leaf Size")
    
    plt.ylabel("RMSE")
    plt.legend()
    plt.savefig('experiment_1.png')
    plt.clf()

    # Experiment 2
    insample_rmse = []
    outsample_rmse = []
    # insample_corr = []
    # outsample_corr = []
    for i in leaf_size:
        bl = bgl.BagLearner(dtl.DTLearner, kwargs={'leaf_size': i}, verbose=True)
        bl.add_evidence(train_x, train_y)  # train it

        # evaluate in sample
        pred_y = bl.query(train_x)  # get the predictions
        rmse = math.sqrt(((train_y - pred_y) ** 2).sum() / train_y.shape[0])
        insample_rmse.append(rmse)
        # c = np.corrcoef(pred_y, y=train_y)
        # corr = c[0, 1]
        # insample_corr.append(corr)

        # evaluate out of sample
        pred_y = bl.query(test_x)  # get the predictions
        rmse = math.sqrt(((test_y - pred_y) ** 2).sum() / test_y.shape[0])
        outsample_rmse.append(rmse)
        # c = np.corrcoef(pred_y, y=test_y)
        # corr = c[0, 1]
        # outsample_corr.append(corr)

    file.write('Experiment 2: Bag Learner\n')
    file.write("\n")
    file.write('leaf_size,dt_insample_rmse,dt_outsample_rmse\n')
    for i in leaf_size:
        file.write(f"{i},{insample_rmse[i-1]},{outsample_rmse[i-1]}\n")
    file.write("\n")
    file.write("\n")

    plt.title("Experiment 2 BagLearner: Leaf Size vs RMSE")
    ins = plt.plot(leaf_size, insample_rmse, color='orange')
    ins[0].set_label('in sample')
    out = plt.plot(leaf_size, outsample_rmse, color='blue')
    out[0].set_label('out of sample')
    plt.xlabel("Leaf Size")

    plt.ylabel("RMSE")
    plt.legend()
    plt.savefig('experiment_2.png')
    plt.clf()

    # Experiment 3 DTLearner
    dt_insample_mae = []
    dt_outsample_mae = []
    dt_insample_r2 = []
    dt_outsample_r2 = []
    for i in leaf_size:
        bl = dtl.DTLearner(leaf_size=i, verbose=True)
        bl.add_evidence(train_x, train_y)  # train it

        # evaluate in sample
        pred_y = bl.query(train_x)  # get the predictions
        mae = np.mean(np.abs(train_y - pred_y))
        dt_insample_mae.append(mae)
        r2 = r_squared(pred_y, train_y)
        dt_insample_r2.append(r2)

        # evaluate out of sample
        pred_y = bl.query(test_x)  # get the predictions
        mae = np.mean(np.abs(test_y - pred_y))
        dt_outsample_mae.append(mae)
        r2 = r_squared(test_y, pred_y)
        dt_outsample_r2.append(r2)

    # Experiment 3 RTLearner
    rt_insample_r2 = []
    rt_outsample_r2 = []
    rt_train_time = []
    for i in leaf_size:
        rl = rtl.RTLearner(leaf_size=i, verbose=True)
        st = time.time()
        rl.add_evidence(train_x, train_y)  # train it
        et = time.time()
        rt_train_time.append(et - st)

        # evaluate in sample
        pred_y = rl.query(train_x)  # get the predictions
        r2 = r_squared(pred_y, train_y)
        rt_insample_r2.append(r2)

        # evaluate out of sample
        pred_y = rl.query(test_x)  # get the predictions
        r2 = r_squared(pred_y, test_y)
        rt_outsample_r2.append(r2)

    plt.title("Experiment 3: Leaf Size vs Train Time")
    ins1 = plt.plot(leaf_size, dt_train_time, color='orange')
    ins1[0].set_label('DTLearner')
    out1 = plt.plot(leaf_size, rt_train_time, color='blue')
    out1[0].set_label('RTLearner')
    plt.xlabel("Leaf Size")
    
    plt.ylabel("Train Time")
    plt.legend()
    plt.savefig('experiment_3a.png')
    plt.clf()

    plt.title("Experiment 3: Leaf Size vs R-Squared")
    ins1 = plt.plot(leaf_size, dt_insample_r2, color='orange')
    ins1[0].set_label('DTLearner: in sample')
    ins2 = plt.plot(leaf_size, rt_insample_r2, color='red')
    ins2[0].set_label('RTLearner: in sample')
    out1 = plt.plot(leaf_size, dt_outsample_r2, color='blue')
    out1[0].set_label('DTLearner: out of sample')
    out2 = plt.plot(leaf_size, rt_outsample_r2, color='green')
    out2[0].set_label('RTLearner: out of sample')
    plt.xlabel("Leaf Size")
    
    plt.ylabel("R-Squared")
    plt.legend()
    plt.savefig('experiment_3b.png')
    plt.clf()

    file.write('Experiment 3: DTLearner vs RTLearner\n')
    file.write("\n")
    file.write(",".join([
        "leaf_size",
        "dt_train_time",
        "rt_train_time",
        "dt_insample_r2",
        "rt_insample_r2",
        "dt_outsample_r2",
        "rt_outsample_r2\n"]))
    for i in leaf_size:
        file.write(",".join([
            f"{i}",
            f"{dt_train_time[i-1]}",
            f"{rt_train_time[i-1]}",
            f"{dt_insample_r2[i-1]}",
            f"{rt_insample_r2[i-1]}",
            f"{dt_outsample_r2[i-1]}",
            f"{rt_outsample_r2[i-1]}\n"]))
    file.flush()
    file.close()
