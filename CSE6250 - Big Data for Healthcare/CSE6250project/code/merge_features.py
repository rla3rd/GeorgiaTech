import sys
import pickle
import glob
import pandas as pd
import numpy as np
from argparse import ArgumentParser


if __name__ == '__main__':

    parser = ArgumentParser()

    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        dest="mode",
        help='cassette or telemetry or file',
        default=None)

    parser.add_argument(
        "-t",
        "--type",
        type=str,
        dest="type",
        help='output type pickle or parquet',
        default='pickle')

    parser.add_argument(
        "-f",
        "--file",
        action='append',
        dest="files",
        help='files to be merged',
        default=[])

    parser.add_argument(
        "-d",
        "--debug",
        action='store_true',
        dest='debug',
        help='debug print mode',
        default=False)

    options = parser.parse_args()
    if options.mode in ('cassette', 'telemetry'):
        loc = f'../data/{options.mode}.*.pkl'
        files = glob.glob(loc)
    else:
        files = None

    if options.files != []:
        files = [f"../data/{f}" for f in options.files]

    merged_df = None
    i = 1
    for f in files:
        data = pickle.load(open(f, "rb"))
        if merged_df is None:
            merged_df = pd.DataFrame(data, columns=['recording', 'time', 'X', 'y'])
        else:
            df = pd.DataFrame(data, columns=['recording', 'time', 'X', 'y'])
            df.drop(columns=['y'], inplace=True)
            merged_df = merged_df.merge(df, on=['recording', 'time'], how='inner', suffixes=("", f"_{i}"))
        i += 1
    merged_df.rename(columns={'X': 'X_1'}, inplace=True)
    for j in range(1, i):
        if merged_df[f'X_{j}'].loc[0].ndim == 1:
            dfc = merged_df.copy()
            cols = []
            for k in range(merged_df[f'X_{j}'].loc[0].shape[0]):
                cols.append(f'X_{j}_{k}')
            dfc[cols] = pd.DataFrame(dfc[f'X_{j}'].tolist(), index=dfc.index)
            merged_df = pd.concat((merged_df, dfc[cols]), axis=1)
            merged_df = merged_df.drop(columns=[f'X_{j}'])

    if options.type == 'pickle':
        if options.mode in ('cassette', 'telemetry'):
            outfile = f'../data/{options.mode}.pkl'
        else:
            if len(files) == 1:
                outfile = f'../data/merged-{options.files[0]}'
            else:
                outfile = f'../data/merged-output.pkl'
        merged_df.to_pickle(outfile)
    else:
        if options.mode in ('cassette', 'telemetry'):
            outfile = f'../data/{options.mode}.pkt'
        else:
            if len(files) == 1:
                fn = (options.files[0]).replace('pkl', 'pqt')
                outfile = f'../data/merged-{fn}'
            else:
                outfile = f'../data/merged-output.pkt'
        merged_df.to_parquet(outfile)
    print(merged_df)
    print(outfile)
