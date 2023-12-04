""""""  		  	   		   	 		  		  		    	 		 		   		 		  
"""Assess a betting strategy.  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
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
  		  	   		   	 		  		  		    	 		 		   		 		  
import numpy as np  
from matplotlib import pyplot as plt


def author():  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    :return: The GT username of the student  		  	   		   	 		  		  		    	 		 		   		 		  
    :rtype: str  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    return "ralbright7"  # replace tb34 with your Georgia Tech username.  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
def gtid():  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    :return: The GT ID of the student  		  	   		   	 		  		  		    	 		 		   		 		  
    :rtype: int  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    return 903548616  # replace with your GT ID number  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
def get_spin_result(win_prob):  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    Given a win probability between 0 and 1, the function returns whether the probability will result in a win.  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
    :param win_prob: The probability of winning  		  	   		   	 		  		  		    	 		 		   		 		  
    :type win_prob: float  		  	   		   	 		  		  		    	 		 		   		 		  
    :return: The result of the spin.  		  	   		   	 		  		  		    	 		 		   		 		  
    :rtype: bool  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    result = False  		  	   		   	 		  		  		    	 		 		   		 		  
    if np.random.random() <= win_prob:  		  	   		   	 		  		  		    	 		 		   		 		  
        result = True  		  	   		   	 		  		  		    	 		 		   		 		  
    return result  	


def experiment_1(runs, win_prob):
    total_bets = 1000
    winnings = np.zeros([runs, total_bets + 1])
    for i in np.arange(runs):
        cash_won = 0
        winnings[i, 0] = 0
        j = 1
        while cash_won < 80:
            won = False
            bet = 1 
            while not won and j <= total_bets:
                won = get_spin_result(win_prob)
                if won:
                    cash_won += bet
                else:
                    cash_won -= bet
                    bet = bet * 2 
                if cash_won > 80:
                    cash_won = 80   
                winnings[i, j] = cash_won
                j += 1      
        winnings[i, j:] = cash_won
    return winnings


def experiment_2(runs, win_prob):
    total_bets = 1000
    winnings = np.zeros([runs, total_bets + 1])
    for i in np.arange(runs):
        bankroll = 256
        cash_won = 0
        winnings[i, 0] = 0
        j = 1
        while cash_won < 80 and bankroll > 0:
            won = False
            bet = 1 
            while not won and j <= total_bets:
                won = get_spin_result(win_prob)
                if won:
                    cash_won += bet
                    bankroll += bet
                else:
                    cash_won -= bet
                    bankroll -= bet
                    bet = bet * 2 
                if bet > bankroll:
                    bet = bankroll
                winnings[i, j] = cash_won
                j += 1      
        winnings[i, j:] = cash_won
    return winnings


		  	   		   	 		  		  		    	 		 		   		 		  		  	   		   	 		  		  		    	 		 		   		 		  
def test_code():  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    Method to test your code  		  	   		   	 		  		  		    	 		 		   		 		  
    """  		  	   		   	 		  		  		    	 		 		   		 		  
    win_prob = 0.47368421055124654  # set appropriately to the probability of a win  		  	   		   	 		  		  		    	 		 		   		 		  
    np.random.seed(gtid())  # do this only once  		  	   		   	 		  		  		    	 		 		   		 		  
    print(get_spin_result(win_prob))  # test the roulette spin  		  	   		   	 		  		  		    	 		 		   		 		  
    # add your code here to implement the experiments  	

    file_name = 'p1_results.txt'
    file = open(file_name, 'w')
    

    # figure 1
    winnings_1 = experiment_1(10, win_prob)
    winnings_1 = winnings_1.transpose()
    plt.plot(winnings_1)
    plt.title("10 Episodes of Winnings")
    plt.xlim([0, 300])
    plt.xlabel("Spins")
    plt.ylim([-256, 100])
    plt.ylabel("Winnings")
    plt.savefig('figure_1.png')
    plt.clf() 

    # figure 2
    winnings_1 = experiment_1(1000, win_prob)
    winnings_1 = winnings_1.transpose()
    mean_1 = winnings_1.mean(axis=1)
    std_1 = winnings_1.std(axis=1)
    plt.plot(mean_1)
    plt.plot(mean_1 + std_1)
    plt.plot(mean_1 - std_1)
    plt.title("Winnings Mean +/- 1 Std Dev")
    plt.xlim([0, 300])
    plt.xlabel("Spins")
    plt.ylim([-256, 100])
    plt.ylabel("Mean Winnings")
    plt.savefig('figure_2.png')
    plt.clf()

    # figure 3
    median_1 = np.median(winnings_1, axis=1)
    plt.plot(median_1)
    plt.plot(median_1 + std_1)
    plt.plot(median_1 - std_1)
    plt.title("Winnings Median +/- 1 Std Dev")
    plt.xlim([0, 300])
    plt.xlabel("Spins")
    plt.ylim([-256, 100])
    plt.ylabel("Median Winnings")
    plt.savefig('figure_3.png')
    plt.clf()

    file.write(f"Experiment 1 Winnings: \n")
    np.savetxt(file, winnings_1, fmt='%.0f', delimiter='|')
    file.write(f"\n")
    file.write(f"Experiment 1 Mean: \n")
    np.savetxt(file, mean_1, fmt='%.4f', delimiter='|')
    file.write(f"\n")
    file.write(f"Experiment 1 Std Dev: \n")
    np.savetxt(file, std_1, fmt='%.4f', delimiter='|')
    file.write(f"\n")

   # figure 4
    winnings_2 = experiment_2(1000, win_prob)
    winnings_2 = winnings_2.transpose()
    mean_2 = winnings_2.mean(axis=1)
    std_2 = winnings_2.std(axis=1)
    plt.plot(mean_2)
    plt.plot(mean_2 + std_2)
    plt.plot(mean_2 - std_2)
    plt.title("Winnings Mean +/- 1 Std Dev")
    plt.xlim([0, 300])
    plt.xlabel("Spins")
    plt.ylim([-256, 100])
    plt.ylabel("Average Winnings")
    plt.savefig('figure_4.png')
    plt.clf()

    # figure 5
    median_2 = np.median(winnings_2, axis=1)
    plt.plot(median_2)
    plt.plot(median_2 + std_2)
    plt.plot(median_2 - std_2)
    plt.title("Winnings Median +/- 1 Std Dev")
    plt.xlim([0, 300])
    plt.xlabel("Spins")
    plt.ylim([-256, 100])
    plt.ylabel("Median Winnings")
    plt.savefig('figure_5.png')
    plt.clf()

    file.write(f"Experiment 2 Winnings: \n")
    np.savetxt(file, winnings_2, fmt='%.0f', delimiter='|')
    file.write(f"\n")
    file.write(f"Experiment 2 Mean: \n")
    np.savetxt(file, mean_2, fmt='%.4f', delimiter='|')
    file.write(f"\n")
    file.write(f"Experiment 2 Std Dev: \n")
    np.savetxt(file, std_2, fmt='%.4f', delimiter='|')
    file.write(f"\n")  	

    file.write("Question 1 (Probablility of Winning $80): \n")
    file.write(f"{np.where(winnings_1[1000, :] == 80, 1, 0).sum()/1000}\n")
    file.write(f"\n")

    file.write("Question 2 (Expected Value): \n")	 
    file.write(f"{winnings_1[1000, :].mean()}\n")
    file.write(f"\n")

    file.write("Question 3 (Std Dev Line Convergence): \n")
    file.write(f"Upper Line Max: {np.max(mean_1 + std_1)}\n")
    file.write(f"Upper Line Min: {np.min(mean_1 + std_1)}\n")
    file.write(f"Lower Line Max: {np.max(mean_1 - std_1)}\n")
    file.write(f"Lower Line Min: {np.min(mean_1 - std_1)}\n")
    file.write(f"\n")

    file.write("Question 4 (Probablility of Winning $80): \n")
    file.write(f"{np.where(winnings_2[1000, :] == 80, 1, 0).sum()/1000}\n")
    file.write(f"\n")

    file.write("Question 5 (Expected Value): \n")	 
    file.write(f"{winnings_2[1000, :].mean()}\n")
    file.write(f"\n")

    file.write("Question 6 (Std Dev Line Convergence): \n")
    std_max = np.max(mean_2 + std_2)
    max_idx = np.argmax(mean_2 + std_2)
    std_min = np.min(mean_2 - std_2)
    min_idx = np.argmin(mean_2 - std_2)
    file.write(f"Upper Line Max: {std_max} @ {max_idx}\n")
    file.write(f"Upper Line Min: {np.min(mean_2 + std_2)}\n")
    file.write(f"Lower Line Max: {np.max(mean_2 - std_2)}\n")
    file.write(f"Lower Line Min: {std_min} @ {min_idx}\n")
    file.write(f"Mean at {max_idx}: {mean_2[max_idx]}\n")
    file.write(f"Mean at {min_idx}: {mean_2[min_idx]}\n")
    file.write(f"\n")

    file.flush()
    file.close()   	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
if __name__ == "__main__":  	
    test_code()  		  	   		   	 		  		  		    	 		 		   		 		  
