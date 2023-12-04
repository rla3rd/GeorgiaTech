import pandas as pd
import numpy as np
import datetime as dt
from util import get_data


def author(self):
    return "ralbright7"


def testPolicy(
    symbol="AAPL",
    sd=dt.datetime(2010, 1, 1),
    ed=dt.datetime(2011, 12, 31),
    sv=100000
):
    # look forward one days returns
    # and determine to be long or short 1000 shares
    df = get_data([symbol], pd.date_range(sd, ed, freq='B'), addSPY=False)
    df = df.sort_index()
    # fwd fill then backfill
    df.fillna(method='ffill', inplace=True)
    df.fillna(method='bfill', inplace=True)
    # normalize prices
    norm_df = df / df.iloc[0]
    # get tomorrows return difference
    norm_df = norm_df.diff().shift(-1)
    # use sign function to determine position (-1, 0, 1)
    positions = np.sign(norm_df) * 1000
    positions.fillna(method='ffill', inplace=True)
    # back into trades by taking diff of positions
    trades = positions.diff()
    trades.fillna(0, inplace=True)
    trades.columns = ['Shares']
    # we only want where the shares changes
    trades = trades[trades['Shares'] != 0]

    orders = trades.copy()
    orders.index.name = 'Date'
    orders.reset_index(inplace=True)
    orders['Symbol'] = symbol
    orders['Order'] = 'BUY'
    sell_idx = orders['Shares'] < 0
    orders.loc[sell_idx, ['Order']] = 'SELL'
    orders['Shares'] = np.abs(orders['Shares'])

    # add a buy of 0 shares onto the dataframe to get to the 1st day
    orders = orders.append({
        'Symbol': symbol,
        'Order': 'BUY',
        'Shares': 0,
        'Date': sd}, ignore_index=True)

    # add a buy of 0 shares onto the dataframe to get to the last day
    orders = orders.append({
        'Symbol': symbol,
        'Order': 'BUY',
        'Shares': 0,
        'Date': ed}, ignore_index=True)

    # sort orders then return
    orders.sort_values(by=['Date'])
    return orders
