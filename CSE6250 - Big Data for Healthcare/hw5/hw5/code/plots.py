import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics import plot_confusion_matrix

def plot_learning_curves():
	jj

def plot_learning_curves(
	train_losses,
	valid_losses,
	train_accuraciesm
	valid_accuracies
){}
	train_losses,
	valid_losses,
	train_accuracies,
	valid_accuracies
):
	plt.figure()
	plt.plot(train_losses)
	plt.plot(valid_losses)
	plt.title('Model Loss')
	plt.ylabel('Loss')
	plt.xlabel('Epoch')
	plt.legend(['Training', 'Validation'], loc='upper left')
	plt.savefig('losses.png')

	plt.figure()
	plt.plot(train_accuracies)
	plt.plot(valid_accuracies)
	plt.title('Model Accuracy')
	plt.ylabel('Accuracy')
	plt.xlabel('Epoch')
	plt.legend(['Training', 'Validation'], loc='upper left')
	plt.savefig('accuracies.png')


def plot_classification_report(results, class_names):
	# TODO: Make a confusion matrix plot.
	# TODO: You do not have to return the plots.
	# TODO: You can save plots as files by codes here or an interactive way according to your preference.
	truth = []
	pred = []
	for r in results:
		truth.append(r[0])
		pred.append(r[1])
	plt.figure()
	cls = classification_report(truth, pred, target_names=class_names, output_dict=True)

	df = pd.DataFrame(cls).iloc[:, :].T
	ax = sns.heatmap(df, annot=True, fmt=".2f", cmap="OrRd", cbar=False)
	ax.figure.subplots_adjust(left = 0.2)
	plt.title('Classification Report')
	plt.savefig('classification_report.png')


def plot_confusion_matrix(results, class_names):
	# TODO: Make a confusion matrix plot.
	# TODO: You do not have to return the plots.
	# TODO: You can save plots as files by codes here or an interactive way according to your preference.
	truth = []
	pred = []
	for r in results:
		truth.append(r[0])
		pred.append(r[1])
	plt.figure()
	cls = classification_report(truth, pred, target_names=class_names, output_dict=True)

	df = pd.DataFrame(cls).iloc[:, :].T
	ax = sns.heatmap(df, annot=True, fmt=".2f", cmap="OrRd", cbar=False)
	ax.figure.subplots_adjust(left = 0.2)
	plt.title('Classification Report')
	plt.savefig('classification_report.png')


	mat = confusion_matrix(truth, pred)
	mat = mat.astype('float') / mat.sum(axis=1)[:, np.newaxis]
	# plt.figure(figsize=(6, 4))
	plt.figure()
	ax = sns.heatmap(mat, annot=True, fmt=".2f", cmap="OrRd", xticklabels=class_names, yticklabels=class_names)
	ax.figure.subplots_adjust(left = 0.2, bottom = 0.25)
	plt.xlabel('Predicted Label')
	plt.xticks(rotation = 45)
	plt.ylabel('True Label')
	plt.title('Normalized Confusion Matrix')
	plt.savefig('confusion_matrix.png')