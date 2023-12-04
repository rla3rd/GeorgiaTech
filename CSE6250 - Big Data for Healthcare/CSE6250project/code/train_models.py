import pandas as pd
from helper import splitdata
from helper import gettensordata
from torch.utils.data import DataLoader
import torch.optim as optim
import torch
from utils import train, evaluate
import torch.nn as nn
from mymodels import MyCNN
import os
from plots import plot_learning_curves
from plots import plot_confusion_matrix
from plots import plot_classification_report
from argparse import ArgumentParser


if __name__ == '__main__':

    parser = ArgumentParser()

    parser.add_argument(
        "-p",
        "--path",
        type=str,
        dest="path",
        default=os.path.join('..', 'data'),
        help="Directory on which to train the model")

    parser.add_argument(
        "-b",
        "--batch",
        type=int,
        dest="batch",
        default=32,
        help="batch size (32)")

    parser.add_argument(
        "-e",
        "--epochs",
        type=int,
        dest="epochs",
        default=20,
        help="epoch size (20)")

    parser.add_argument(
        "-d",
        "--dropout",
        action='store_true',
        dest="dropout",
        default=False,
        help="use dropout ratio")

    options = parser.parse_args()

    data_folder = options.path

    _, _, myfiles = next(os.walk(data_folder))

    myfiles = [x for x in myfiles if 'tar' not in x and '2d' not in x]

    accuracydict = {
        x.replace(
            'merged-cassette.eeg', '').replace(
                '.pkl', '').replace(
                    '.', '_'): 0.0 for x in myfiles}

    NUM_WORKERS = 0
    BATCH_SIZE = options.batch
    NUM_EPOCHS = options.epochs
    PATH_OUTPUT = os.path.join('..', 'output')

    for file in myfiles:
        name = file.replace(
            'merged-cassette.eeg', '').replace(
                '.pkl', '').replace(
                    '.', '_')
        df = pd.read_pickle(os.path.join(data_folder, file))
        model = MyCNN(df.shape[1]-3, use_dropout=options.dropout)
        df_train, df_val, df_test = splitdata(df)
        train_dataset = gettensordata(df_train)
        valid_dataset = gettensordata(df_val)
        test_dataset = gettensordata(df_test)
        train_loader = torch.utils.data.DataLoader(
            train_dataset,
            batch_size=BATCH_SIZE,
            shuffle=True,
            num_workers=NUM_WORKERS)
        valid_loader = torch.utils.data.DataLoader(
            valid_dataset,
            batch_size=BATCH_SIZE,
            shuffle=False,
            num_workers=NUM_WORKERS)
        test_loader = torch.utils.data.DataLoader(
            test_dataset,
            batch_size=BATCH_SIZE,
            shuffle=False,
            num_workers=NUM_WORKERS)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters())

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        model.to(device)
        criterion.to(device)

        best_val_acc = 0.0
        train_losses, train_accuracies = [], []
        valid_losses, valid_accuracies = [], []

        for epoch in range(NUM_EPOCHS):
            train_loss, train_accuracy = train(
                model,
                device,
                train_loader,
                criterion,
                optimizer,
                epoch)
            valid_loss, valid_accuracy, valid_results = evaluate(
                model,
                device,
                valid_loader,
                criterion)

            train_losses.append(train_loss)
            valid_losses.append(valid_loss)

            train_accuracies.append(train_accuracy)
            valid_accuracies.append(valid_accuracy)

            # let's keep the model that has the best accuracy,
            # but you can also use another metric.
            is_best = valid_accuracy > best_val_acc
            if is_best:
                best_val_acc = valid_accuracy
                torch.save(
                    model,
                    os.path.join(PATH_OUTPUT, f'mycnn{name}'),
                    _use_new_zipfile_serialization=False)

        plot_learning_curves(
            train_losses,
            valid_losses,
            train_accuracies,
            valid_accuracies,
            name)

        best_model = torch.load(os.path.join(PATH_OUTPUT, f'mycnn{name}'))
        test_loss, test_accuracy, test_results = evaluate(
            best_model,
            device,
            test_loader,
            criterion)
        class_names = ['WAKE', 'STAGE 1', 'STAGE 2', 'STAGE 3,4', 'STAGE R']
        plot_confusion_matrix(test_results, class_names, name)
        plot_classification_report(test_results, class_names, name)
        accuracydict[name] = best_val_acc

    for k, v in accuracydict.items():
        print("best accuracy of {} data is ".format(k), v)
