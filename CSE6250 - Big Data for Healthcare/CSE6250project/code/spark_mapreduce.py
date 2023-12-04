# Load libraries
import sys
import glob
import numpy as np
import pickle
import mne
from mne.preprocessing import ICA
import warnings
import traceback
import findspark
import pyspark
from pyspark.sql import SparkSession
from pyspark.sql import SQLContext
from transforms import eeg_psd_welch
from transforms import eeg_psd_multitaper
from transforms import eeg_tfr_morlet
from mappings import cassette_mapping
from mappings import telemetry_mapping
from mappings import annotation_desc_2_event_id
from mappings import event_ids
from argparse import ArgumentParser

warnings.filterwarnings("ignore", category=RuntimeWarning) 

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


def load_edf(data):
    r_idx = data[0]
    raw_edf = data[1]
    raw_annot = data[2]
    transformer = data[3]
    args = data[4]

    raw = mne.io.read_raw_edf(raw_edf, verbose='warning', preload=True)
    raw.filter(0.5, 49.5, fir_design='firwin')
    annot = mne.read_annotations(raw_annot)

    raw.set_annotations(annot, emit_warning=False)

    if options.mode == 'telemetry':
        mapped = telemetry_mapping
    else:
        mapped = cassette_mapping

    raw.set_channel_types(mapped, verbose='warning')

    events, _ = mne.events_from_annotations(
        raw,
        event_id=annotation_desc_2_event_id,
        chunk_duration=30.,
        verbose='warning')

    r_idx = np.array([r_idx] * events.shape[0])

    tmax = 30. - 1. / raw.info['sfreq']

    try:
        epochs = mne.Epochs(
            raw=raw,
            events=events,
            event_id=event_ids,
            tmin=0.,
            tmax=tmax,
            baseline=None,
            picks=['eeg'],
            on_missing='ignore',
            verbose='warning',
            preload=True)

        fwd = 0
        for i in range(len(events[:, 2])):
            if events[i, 2] == 1:
                fwd += 1
            else:
                break

        bwd = 0
        for i in range(1, len(events[:, 2])+1):
            if events[-i, 2] == 1:
                bwd += 1
            else:
                break
        
        limit = 30
        if fwd > limit:
            fwd = fwd - limit
        else:
            fwd = 0

        if bwd > limit:
            bwd = bwd - limit
        else:
            bwd = 1

        epochs = epochs[fwd:-bwd]

        epochs.drop_bad()
        y = epochs.events[:, 2]
        if args is None:
            ev, transformed, y = transformer(epochs, y)
        else:
            ev, transformed, y = transformer(epochs, y, args=args)

        # combine inputs and labels into the rdd
        transformed_y = np.array(list(zip(r_idx, ev, transformed, y)))
        return transformed_y

    except Exception:
        error = sys.exc_info()[0]
        details = traceback.format_exc()
        print(error, details)
        sys.exit(1)


if __name__ == '__main__':

    sc = spark.sparkContext

    parser = ArgumentParser()
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        dest="mode",
        help='cassette or telemetry',
        default='cassette')

    parser.add_argument(
        "-t",
        "--transform",
        type=str,
        dest='transform',
        help='transform function name',
        default=None)

    parser.add_argument(
        "-s",
        "--stats",
        type=str,
        dest='stats',
        help='stats mode(median, mean)',
        default=False)

    parser.add_argument(
        "-d",
        "--debug",
        action='store_true',
        dest='debug',
        help='debug print mode',
        default=False)

    options = parser.parse_args()

    if options.mode not in ('cassette', 'telemetry'):
        print('Invalid Mode')
        sys.exit(1)

    if options.transform == 'eeg_psd_welch':
        transformer = eeg_psd_welch
    elif options.transform == 'eeg_psd_multitaper':
        transformer = eeg_psd_multitaper
    elif options.transform == 'eeg_tfr_morlet':
        transformer = eeg_tfr_morlet
    else:
        print('no valid transformer')
        sys.exit(1)

    # Assuming a setup similar to the hw assignments where there is a code
    # and data folder in the same directory
    path = "../data/sleep-edf-database-expanded-1.0.0"
    loc = f'{path}/sleep-{options.mode}/*.edf'

    files = np.array(glob.glob(loc))

    # Filenames are ST7ssNID-T.edf where
    # ST7 is a placeholder
    # ss is the patient number
    # N is the night
    # ID is the recorder ID
    # T is the type being PSG or Hypnogram

    # sets are unordered so cast to a list and sort
    file_identifier = sorted(list(set(
        [f.split('/')[-1].split('-')[0][0:-2] for f in files])))

    r_idx = {}
    i = 0
    for recording in file_identifier:
        r_idx[recording] = i
        i += 1

    file_boolean_setup = np.array(
        [f.split('/')[-1].split('-')[0][0:-2] for f in files])
    files_grpd = [
        files[file_boolean_setup == ident] for ident in file_identifier]

    ignored_files = []
    jobs = []

    for file in files_grpd:
        if 'Hypnogram' in file[0]:
            tmp = file[1]
            file[1] = file[0]
            file[0] = tmp
        raw_edf = file[0]
        raw_annot = file[1]
        ident = file[0].split('/')[-1].split('-')[0][0:-2]
        data = [r_idx[ident], raw_edf, raw_annot, transformer, options.stats]
        jobs.append(data)

    jobs_rdd = sc.parallelize(jobs)
    res_rdd = jobs_rdd.flatMap(lambda x: load_edf(x))
    results = np.array(res_rdd.filter(lambda x: x != np.array([])).collect())
    print(f"Transform shape: {results[0, 2].shape}")
    print(f"Results shape: {results.shape}")
    if options.stats is None:
        outfile = f"../data/{options.mode}.{options.transform}.pkl"
    else:
        outfile = f"../data/{options.mode}.{options.transform}.{options.stats}.pkl"
    print(f"Output: {outfile}")
    pickle.dump(results, open(outfile, 'wb'))
