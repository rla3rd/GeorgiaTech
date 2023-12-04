from helper import getshape
from helper import convertrgba
from torch.utils.data import DataLoader
import torch.optim as optim
import torch
from utils import train
from utils import evaluate
import torch.nn as nn
from mymodels import MyCNN2D
import os
import sys
import traceback
from plots import plot_learning_curves
from plots import plot_confusion_matrix
from plots import plot_classification_report
from torchvision import transforms
import torchvision
from sklearn.model_selection import train_test_split
import findspark
import pyspark
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from argparse import ArgumentParser

# Find and initialize spark
findspark.init()

spark = SparkSession \
    .builder \
    .master('local[*]') \
    .config("spark.cores.max", "8") \
    .config("spark.executor.cores", "2") \
    .config("spark.driver.memory", "28g") \
    .config("spark.execute.memory", "28g") \
    .config('spark.driver.maxResultSize', '2g') \
    .appName("sleepdata") \
    .getOrCreate()

sc = spark.sparkContext


def convert_image(img_data):
    image = img_data[0]
    train = img_data[1]
    test = img_data[2]
    valid = img_data[3]
    folders = img_data[4]

    label = image.split('_')[1].split('.png')[0]
    if image in train:
        out_path = os.path.join(folders[0], labels[label], image)
    elif image in valid:
        out_path = os.path.join(folders[2], labels[label], image)
    elif image in test:
        out_path = os.path.join(folders[1], labels[label], image)

    convertrgba(
        os.path.join(pictures_folder, image),
        out_path)

    return out_path


if __name__ == '__main__':
    try:
        parser = ArgumentParser()

        parser.add_argument(
            "-p",
            "--path",
            type=str,
            dest="path",
            default=os.path.join('..', 'data'),
            help="Directory on which to train the model")

        parser.add_argument(
            "-s",
            "--split",
            action="store_true",
            default=False,
            dest="splitfiles",
            help="split files into train/test/valid folders")

        parser.add_argument(
            "-b",
            "--batch",
            type=int,
            dest="batch",
            default=64,
            help="batch size (64)")

        parser.add_argument(
            "-e",
            "--epochs",
            type=int,
            dest="epochs",
            default=20,
            help="epoch size (20)")

        options = parser.parse_args()

        project_data = options.path
        pictures_folder = os.path.join(project_data, 'cassette')

        train_folder = os.path.join(project_data, 'train')
        valid_folder = os.path.join(project_data, 'valid')
        test_folder = os.path.join(project_data, 'test')

        folders = [train_folder, test_folder, valid_folder]

        # run this only once to segment the images on your disk
        if options.splitfiles:

            _, _, myfiles = next(os.walk(pictures_folder))

            # shape of the images
            myfiles = [file for file in myfiles if getshape(
                os.path.join(pictures_folder, file)) == (389, 128, 4)]
            traind, valid = train_test_split(myfiles, test_size=0.4)
            valid, test = train_test_split(valid, test_size=0.5)

            labels = {
                '1': 'WAKE',
                '2': 'STAGE 1',
                '3': 'STAGE 2',
                '4': 'STAGE 3,4',
                '5': 'STAGE R'}

            for paths in [train_folder, valid_folder, test_folder]:
                if not os.path.exists(paths):
                    os.mkdir(paths)
                for _, v in labels.items():
                    if not os.path.exists(os.path.join(paths, v)):
                        os.mkdir(os.path.join(paths, v))
            jobs = []
            for image in myfiles:
                jobs.append([image, traind, test, valid, folders])
            jobs_rdd = sc.parallelize(jobs)
            res_rdd = jobs_rdd.flatMap(lambda x: convert_image(x))
            results = res_rdd.collect()

        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print("Currently using ", device)

        # transform images
        transformer = transforms.Compose([
            transforms.ToTensor(),  # 0-255 to 0-1 numpy to tensors
            transforms.Normalize(
                [0.5, 0.5, 0.5],
                [0.5, 0.5, 0.5])
            ])

        # dataloader
        NUM_WORKERS = 0
        BATCH_SIZE = options.batch
        NUM_EPOCHS = options.epochs
        PATH_OUTPUT = os.path.join('..', 'output')

        model = MyCNN2D((389, 128, 4))

        accuracydict = {}
        train_loader = DataLoader(
            torchvision.datasets.ImageFolder(
                train_folder,
                transform=transformer),
            batch_size=BATCH_SIZE,
            shuffle=True,
            num_workers=NUM_WORKERS)

        valid_loader = DataLoader(
            torchvision.datasets.ImageFolder(
                valid_folder,
                transform=transformer),
            batch_size=BATCH_SIZE,
            shuffle=True,
            num_workers=NUM_WORKERS)

        test_loader = DataLoader(
            torchvision.datasets.ImageFolder(
                test_folder,
                transform=transformer),
            batch_size=BATCH_SIZE,
            shuffle=True,
            num_workers=NUM_WORKERS)

        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(model.parameters())

        model.to(device)
        criterion.to(device)

        best_val_acc = 0.0
        train_losses, train_accuracies = [], []
        valid_losses, valid_accuracies = [], []

        name = 'cassette_sg'

        for epoch in range(NUM_EPOCHS):
            train_loss, train_accuracy = train(
                model,
                device,
                train_loader,
                criterion,
                optimizer,
                epoch)

            valid_loss, valid_accuracy, valid_results = evaluate(
                model, device, valid_loader, criterion)

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
                    os.path.join(PATH_OUTPUT, 'mycnn'+name),
                    _use_new_zipfile_serialization=False)

        plot_learning_curves(
            train_losses,
            valid_losses,
            train_accuracies,
            valid_accuracies,
            name)

        best_model = torch.load(os.path.join(PATH_OUTPUT, 'mycnn'+name))
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

    except Exception:
        error = sys.exc_info()[0]
        details = traceback.format_exc()
        print(error, details)
        sys.exit(1)
