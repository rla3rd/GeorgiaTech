import numpy as np
import pandas as pd
from mne.time_frequency import psd_welch
from mne.time_frequency import psd_multitaper
from mne.time_frequency import tfr_morlet
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=DeprecationWarning) 


# User Defined Functions
def eeg_psd_welch(epochs, y, args=None, debug=False):
    """
    EEG relative power band feature extraction.
    """
    ev = epochs.events[:, 0]

    # specific frequency bands
    step = 0.5
    band_min = 0.5
    band_max = 49.5
    z = list(np.arange(band_min, band_max, step))
    # z = np.logspace(*np.log10([band_min, band_max]), num=49)
    FREQ_BANDS = [[x, x+step] for x in z]

    psds, freqs = psd_welch(
        epochs,
        picks='eeg',
        fmin=band_min,
        fmax=band_max,
        verbose='warning',
        n_jobs=8)

    # Normalize the PSDs
    psds /= np.sum(psds, axis=-1, keepdims=True)

    X = []
    for fmin, fmax in FREQ_BANDS:
        if args == 'mean':
            psds_band = psds[:, :, (freqs >= fmin) & (freqs < fmax)].mean(
                axis=-1)
        else:
            psds_band = np.median(
                psds[:, :, (freqs >= fmin) & (freqs < fmax)], axis=-1)
        X.append(psds_band.reshape(len(psds), -1))

    X = np.concatenate(X, axis=1)

    # remove nan's from the transform
    nan_idx = np.argwhere([np.any(np.isnan(x)) for x in X]).flatten()
    for idx in np.flip(nan_idx):
        X = np.delete(X, idx, axis=0)
        ev = np.delete(ev, idx)
        y = np.delete(y, idx)

    return ev, X, y


def eeg_psd_multitaper(epochs, y, args=None, debug=False):
    """
    EEG relative psd multitaper feature extraction.
    """
    ev = epochs.events[:, 0]

    # specific frequency bands
    step = 0.5
    band_min = 0.5
    band_max = 49.5
    z = list(np.arange(band_min, band_max, step))
    FREQ_BANDS = [[x, x+step] for x in z]

    psds, freqs = psd_multitaper(
        epochs,
        picks='eeg',
        fmin=band_min,
        fmax=band_max,
        verbose='warning',
        n_jobs=8)

    # Normalize the PSDs
    psds /= np.sum(psds, axis=-1, keepdims=True)

    X = []
    for fmin, fmax in FREQ_BANDS:
        if args == 'mean':
            psds_band = psds[:, :, (freqs >= fmin) & (freqs < fmax)].mean(
                axis=-1)
        else:
            psds_band = np.median(
                psds[:, :, (freqs >= fmin) & (freqs < fmax)], axis=-1)
        X.append(psds_band.reshape(len(psds), -1))

    X = np.concatenate(X, axis=1)

    # remove nan's from the transform
    nan_idx = np.argwhere([np.any(np.isnan(x)) for x in X]).flatten()
    for idx in np.flip(nan_idx):
        X = np.delete(X, idx, axis=0)
        ev = np.delete(ev, idx)
        y = np.delete(y, idx)

    return ev, X, y


def eeg_tfr_morlet_per_band(epoch, args=None, debug=False):
    band_min = 0.5
    band_max = 49.5
    if args not in ('mean2d', 'median2d'):
        step = 0.5
        decimals = 25
    else:
        step = 2.0
        decimals = 100
    # frequencies = np.logspace(*np.log10([band_min, band_max]), num=49)
    frequencies = np.arange(band_min, band_max, step)
    n_cycles = frequencies / 2.  # different number of cycle per frequency

    power = tfr_morlet(
        epoch,
        picks="eeg",
        freqs=frequencies,
        n_cycles=n_cycles,
        use_fft=True,
        return_itc=False,
        decim=decimals,
        n_jobs=8,
        verbose='warning')

    data = power.data
    times = power.times
    freqs = power.freqs
    if args == 'mean':
        df = pd.DataFrame(
            np.average(data, axis=0).T, index=times, columns=freqs)
        df = df.mean(axis=1)
    elif args == 'mean2d':
        df = pd.DataFrame(
            np.average(data, axis=0).T, index=times, columns=freqs)
    elif args == 'median':
        df = pd.DataFrame(
            np.median(data, axis=0).T, index=times, columns=freqs)
        df = df.median(axis=1)
    elif args == 'median2d':
        df = pd.DataFrame(
            np.median(data, axis=0).T, index=times, columns=freqs)
    df.index = times
    return df


def eeg_tfr_morlet(epochs, y, args=None, debug=False):
    ev = epochs.events[:, 0]
    y = epochs.events[:, 2]

    events = []
    for i in range(len(epochs)):
        df = eeg_tfr_morlet_per_band(epochs[i], args=args)
        X = df.to_numpy()
        events.append(X)

    X = np.array(events)
    return ev, X, y
