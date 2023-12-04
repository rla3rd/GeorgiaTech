import os
import os.path
import glob
import numpy as np
import mne
from mne.time_frequency import psd_welch
import findspark
import pyspark
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from mappings import cassette_mapping
from mappings import telemetry_mapping
from mappings import annotation_desc_2_event_id
from mappings import event_ids
import matplotlib
import matplotlib.pyplot as plt

findspark.init()

spark = SparkSession \
    .builder \
    .master('local[7]') \
    .config("spark.driver.memory", "8g") \
    .appName("sleepdata") \
    .getOrCreate()


def generate_psd(file_grp, channel_types):
    # Parse out raw and annotation
    for file in file_grp:
        file_type = file.split('/')[-1].split('-')[1].split('.')[0]
        if file_type == 'PSG':
            raw = mne.io.read_raw_edf(file)
        elif file_type == 'Hypnogram':
            annot = mne.read_annotations(file)
        else:
            raise Exception("File does not end in 'PSG' or 'Hypnogram'")

    # Set annotation and channel types
    raw.set_annotations(annot, emit_warning=False)
    raw.set_channel_types(channel_types)

    # Get patient identifier
    pat_night = file_grp[0].split('/')[-1].split('-')[0]

    # Get events from annotations
    events, _ = mne.events_from_annotations(
        raw, event_id=annotation_desc_2_event_id, chunk_duration=30.)

    # Get epochs
    tmax = 30. - 1. / raw.info['sfreq'] 
    epochs = mne.Epochs(
        raw=raw,
        events=events,
        event_id=event_ids,
        tmin=0.,
        tmax=tmax,
        baseline=None,
        on_missing='ignore')

    epochs.drop_bad()

    # Get Welch PSD and average between channels
    psds, freq = mne.time_frequency.psd_welch(
        epochs,
        fmin=0.5,
        fmax=49.5,
        n_fft=200,
        n_overlap=100,
        average=None)

    psds = psds.mean(axis=1)

    # Normalize the PSDs
    psds /= np.sum(psds, axis=-1, keepdims=True)

    # File identifier
    file_ident = [
        p + str(e) + '_' + str(r)
        for p, e, r
        in zip(
            [pat_night] * len(psds),
            np.arange(len(psds)),
            epochs.events[:, 2])]

    # Add to accumulator and return
    return list(zip(psds, file_ident))


def generate_plot(psds_ident, files_type):
    matplotlib.use('Agg')
    psd, ident = psds_ident

    # Set filename
    img_file = f'../data/{files_type}/' + ident + '.png'

    # Generate plot
    plt.imshow(psd, interpolation='nearest')
    plt.axis('off')

    # Save plot
    plt.savefig(img_file, bbox_inches='tight')

    # Clear plot
    plt.close()


if __name__ == '__main__':

    sc = spark.sparkContext

    # telemetry or cassette
    files_type = 'cassette'
    channel_types = {
        'telemetry': telemetry_mapping,
        'cassette': cassette_mapping}[files_type]

    fp = f'../data/sleep-edf-database-expanded-1.0.0/sleep-{files_type}/*.edf'
    files = glob.glob(fp)
    files = np.array(files)
    file_identifier = set(
        [f.split('/')[-1].split('-')[0][0:-2] for f in files])
    file_boolean_setup = np.array(
        [f.split('/')[-1].split('-')[0][0:-2] for f in files])
    files_grpd = [
        files[file_boolean_setup == ident] for ident in file_identifier]

    jobs_rdd = sc.parallelize(files_grpd)
    psd_rdd = jobs_rdd.flatMap(lambda x: generate_psd(x, channel_types))

    # This is only needed if you stop the jobs
    # or they fail and you need to restart
    psd_rdd_filter = psd_rdd.filter(
        lambda x: not os.path.isfile(f'../data/{files_type}/{x[1]}.png'))

    # This will start the jobs
    psd_rdd_filter.foreach(lambda x: generate_plot(x, files_type))
