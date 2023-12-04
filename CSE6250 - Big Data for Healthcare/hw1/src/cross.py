import models_partc
from sklearn.model_selection import KFold, ShuffleSplit
from numpy import mean
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import cross_val_score
from sklearn.metrics import roc_auc_score, accuracy_score
import utils

# USE THE GIVEN FUNCTION NAME, DO NOT CHANGE IT

# USE THIS RANDOM STATE FOR ALL OF YOUR CROSS VALIDATION TESTS, OR THE TESTS WILL NEVER PASS
RANDOM_STATE = 545510477

#input: training data and corresponding labels
#output: accuracy, auc
def get_acc_auc_kfold(X,Y,k=5):
	#TODO:First get the train indices and test indices for each iteration
	#Then train the classifier accordingly
	#Report the mean accuracy and mean auc of all the folds
	cv = KFold(n_splits=k, random_state=RANDOM_STATE, shuffle=True)
	model = LogisticRegression(random_state=RANDOM_STATE)

	accs = []
	aucs = []
	for i, (train, test) in enumerate(cv.split(X, Y)):
		model.fit(X[train], Y[train])
		Y_pred = model.predict(X[test])
		acc = accuracy_score(Y[test], Y_pred)
		auc = roc_auc_score(Y[test], Y_pred)
		accs.append(acc)
		aucs.append(auc)
	accuracy = mean(accs)
	auc = mean(aucs)
	return accuracy, auc


#input: training data and corresponding labels
#output: accuracy, auc
def get_acc_auc_randomisedCV(X,Y,iterNo=5,test_percent=0.2):
	#TODO: First get the train indices and test indices for each iteration
	#Then train the classifier accordingly
	#Report the mean accuracy and mean auc of all the iterations
	cv = ShuffleSplit(n_splits=iterNo, test_size=test_percent, random_state=RANDOM_STATE)
	model = LogisticRegression(random_state=RANDOM_STATE)

	accs = []
	aucs = []
	for i, (train, test) in enumerate(cv.split(X, Y)):
		model.fit(X[train], Y[train])
		Y_pred = model.predict(X[test])
		acc = accuracy_score(Y[test], Y_pred)
		auc = roc_auc_score(Y[test], Y_pred)
		accs.append(acc)
		aucs.append(auc)
	accuracy = mean(accs)
	auc = mean(aucs)
	return accuracy, auc


def main():
	X,Y = utils.get_data_from_svmlight("../deliverables/features_svmlight.train")
	print("Classifier: Logistic Regression__________")
	acc_k,auc_k = get_acc_auc_kfold(X,Y)
	print(("Average Accuracy in KFold CV: "+str(acc_k)))
	print(("Average AUC in KFold CV: "+str(auc_k)))
	acc_r,auc_r = get_acc_auc_randomisedCV(X,Y)
	print(("Average Accuracy in Randomised CV: "+str(acc_r)))
	print(("Average AUC in Randomised CV: "+str(auc_r)))

if __name__ == "__main__":
	main()

