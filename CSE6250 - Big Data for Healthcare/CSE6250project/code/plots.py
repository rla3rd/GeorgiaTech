import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix
from sklearn.metrics import ConfusionMatrixDisplay, classification_report, confusion_matrix
import seaborn as sns
import pandas as pd

def plot_learning_curves(train_losses, valid_losses, train_accuracies, valid_accuracies, title):
    plt.plot(train_losses)
    plt.plot(valid_losses)
    plt.title("LossCurve " + title)
    plt.legend(labels=["training losses","validation losses"],loc = 'upper right')
    plt.savefig("../output/losses.jpg", dpi=500)
    plt.close()
    plt.plot(train_accuracies)
    plt.plot(valid_accuracies)
    plt.title("Accuracy curve " +title)
    plt.legend(labels=["training Acc","validation Acc"],loc = 'upper right')
    plt.savefig("../output/accuracies_{}.jpg".format(title), dpi=500)
    plt.close()

def plot_confusion_matrix(results, class_names, title):
    y_true = [x[0] for x in results]
    y_pred = [x[1] for x in results]
    confm = confusion_matrix(y_true,y_pred,normalize='true')
    disp = ConfusionMatrixDisplay(confusion_matrix=confm,display_labels=class_names)
    disp = disp.plot(include_values=True,cmap=plt.cm.Blues, ax=None, xticks_rotation='horizontal')
    fig = plt.gcf()
    fig.set_size_inches(18.5,10.5)
    plt.title("Confusion Matrix " + title)
    plt.savefig('../output/confusionmatrix_{}.jpg'.format(title), dpi=500)
    plt.close()



def plot_classification_report(results, class_names, title):
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
    plt.title('Classification Report '+ title)
    plt.savefig('../output/classification_report_{}.jpg'.format(title), dpi=500)
    plt.close()
