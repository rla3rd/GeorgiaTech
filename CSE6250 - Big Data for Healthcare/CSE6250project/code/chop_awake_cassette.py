# the initial spectograph run did not chop epochs
# since each epoch in each recording is a file
# its faster to just remove the files that need
# trimmed out
import os
import sys
import traceback
import findspark
import pyspark
import numpy as np
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


def chop_epochs(pn):
    try:
        epochs = [x for x in myfiles if x[:8] == pn]
        labels = {
            x.split('_')[0].replace(pn, ''): x.split('_')[1]
            for x in epochs}
        labels = {int(k): v for k, v in labels.items()}
        ordered_labels = [v for k, v in sorted(
            labels.items(), key=lambda item: item[0])]
        indices = []
        for st in ['2.png', '3.png', '4.png', '5.png']:
            if st in ordered_labels:
                indices.append(ordered_labels.index(st))
        sleeponset = min(indices)
        if sleeponset > 30:
            sleeponset = sleeponset - 30  # 15 minute buffer
        wakeup = len(ordered_labels) - ordered_labels[::-1].index('1.png') - 1
        if len(epochs) - wakeup > 30:
            wakeup = wakeup + 30
        # deleting all files before sleeponset and after wake up
        epochbeforesleep = epochs[:sleeponset]
        epochafterwake = epochs[wakeup:]
        epochs_to_delete = epochbeforesleep + epochafterwake

        print("".join([
            f"For patientnight {pn} ",
            f"deleting {len(epochs_to_delete)} ",
            f"epochs from {len(epochs)}, ",
            f"remaining epochs {len(epochs)-len(epochs_to_delete)}"]))

        remaning.append(len(epochs)-len(epochs_to_delete))
        for c, e in enumerate(epochs_to_delete):
            os.remove(os.path.join(data_folder, e))
        return pn
    except Exception:
        error = sys.exc_info()[0]
        details = traceback.format_exc()
        print(error, details)
        sys.exit(1)


if __name__ == '__main__':
    parser = ArgumentParser()

    parser.add_argument(
        "-p",
        "--path",
        type=str,
        dest="path",
        default=os.path.join('..', 'data', 'cassette'),
        help="Directory on which to train the model")

    options = parser.parse_args()
    data_folder = options.path
    _, _, myfiles = next(os.walk(data_folder))

    patientsnight = list(set([x[:8] for x in myfiles]))
    remaning = []
    jobs_rdd = sc.parallelize(patientsnight)
    res_rdd = jobs_rdd.flatMap(lambda x: chop_epochs(x))
    results = np.array(res_rdd.collect())
