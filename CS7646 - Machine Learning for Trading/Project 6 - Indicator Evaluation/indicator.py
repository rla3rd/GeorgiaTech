import pandas as pd
import datetime as dt
from util import get_data
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def author(self):
    return "ralbright7"


# SMA, Bollinger Bands %, EMA, MACD, Momentum
def sma(df, n):
    sma = df.rolling(n).mean()
    return sma


def std(df, n):
    std = df.rolling(n).std()
    return std


def bb_pct(df, n, smooth=5, lvl=2):
    # %B = [(Price – Lower Band) / (Upper Band – Lower Band)] * 100
    mean = sma(df, n)
    p = ema(df, smooth)
    stddev = std(df, n)
    upper = mean + lvl * stddev
    lower = mean - lvl * stddev
    bb_pct = (p - lower) / (upper - lower)
    return bb_pct


def ema(df, n):
    ema = df.ewm(span=n, min_periods=n).mean()
    return ema


def macd(df, fast, slow, signal):
    # typically fast 12 day, slow 26 day, 9 day signal
    ema_slow = ema(df, slow)
    ema_fast = ema(df, fast)
    macd = ema_slow - ema_fast
    macd_signal = ema(macd, signal)
    return macd - macd_signal


def momentum(df, n, smooth=5):
    p = ema(df, smooth)
    m = p / p.shift(n) - 1
    return m


if __name__ == '__main__':
    ticker = "JPM"
    # init date is older than simulation start so we can
    # have populated indicators from day 1
    # we'll trim the dataframes afterwards then normalize
    # by the 1st days price
    init_date = dt.datetime(2007, 1, 1)
    begin_date = dt.datetime(2008, 1, 1)
    end_date = dt.datetime(2009, 12, 31)

    df = get_data(
        [ticker],
        pd.date_range(init_date, end_date, freq='B'),
        addSPY=False)
    df = df.sort_index()
    # fwd fill then backfill
    df.fillna(method='ffill', inplace=True)
    df.fillna(method='bfill', inplace=True)

    # populate our indicators and filter out 2007
    # 50 day simple moving average
    simple = sma(df, 50)
    idx = simple.index.to_series().between(begin_date, end_date)
    simple = simple[idx].copy()

    # 50 day bollinger band pct using 5 day exponential moving avergae
    boll = bb_pct(df, 50)
    boll = boll[idx].copy()

    # 10 day exponential moving average
    ewm = ema(df, 5)
    ewm = ewm[idx].copy()

    # macd, fast 12 day, slow 26 day, 9 day signal
    cross = macd(df, 12, 26, 9)
    cross = cross[idx].copy()

    # 20 day momemntum using 5 day exponential moving average
    mom = momentum(df, 20, smooth=5)
    mom = mom[idx].copy()

    # shorten prices to start of simulation
    df = df[idx].copy()

    # normalize prices and indicators
    n_simple = simple / df.iloc[0]
    n_ewm = ewm / df.iloc[0]
    ndf = df / df.iloc[0]

    # sma chart
    fig, ax = plt.subplots()
    fmt_month = mdates.MonthLocator()
    p = plt.plot(df.index, ndf, color='blue')
    plt.title(f"{ticker} Stock Price vs Simple Moving Average")
    p[0].set_label('Stock Price')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    s = plt.plot(df.index, n_simple, color='red')
    s[0].set_label('SMA (50 days)')
    plt.xlabel("Date")
    plt.ylabel("Normalized Prices")
    plt.legend()
    plt.savefig('JPM_sma.png')
    plt.clf()

    # ema chart
    fig, ax = plt.subplots()
    fmt_month = mdates.MonthLocator()
    p = plt.plot(df.index, ndf, color='blue')
    plt.title(f"{ticker} Stock Price vs Exponential Moving Average")
    p[0].set_label('Stock Price')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    s = plt.plot(df.index, n_ewm, color='red')
    s[0].set_label('EMA(5 days)')
    plt.xlabel("Date")
    plt.ylabel("Normalized Prices")
    plt.legend()
    plt.savefig('JPM_ema.png')
    plt.clf()

    # bollinger band pct
    fig, ax = plt.subplots(2, 1)
    fmt_month = mdates.MonthLocator()
    p = ax[0].plot(df.index, ndf, color='blue')
    ax[0].set_title(f"{ticker} Stock Price vs Bollinger Band Pct")
    ax[0].set_ylabel("Normalized Prices")
    p[0].set_label('Stock Price')
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    s = ax[1].plot(df.index, boll, color='red')
    u = ax[1].plot(df.index, [1] * len(df.index), color='black')
    l = ax[1].plot(df.index, [0] * len(df.index), color='black')
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    ax[1].set_ylabel("Bollinger Band Pct")
    s[0].set_label('Bollinger Band Pct (50 days)')
    plt.xlabel("Date")
    ax[0].legend()
    ax[1].legend()
    plt.savefig('JPM_bollinger.png')
    plt.clf()

    # macd chart
    fig, ax = plt.subplots(2, 1)
    fmt_month = mdates.MonthLocator()
    p = ax[0].plot(df.index, ndf, color='blue')
    ax[0].set_title(f"{ticker} Stock Price vs MACD")
    ax[0].set_ylabel("Normalized Prices")
    p[0].set_label('Stock Price')
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    s = ax[1].plot(df.index, cross, color='red')
    m = ax[1].plot(df.index, [0] * len(df.index), color='black')
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    ax[1].set_ylabel("MACD")
    s[0].set_label('MACD (12, 26, 9)')
    plt.xlabel("Date")
    ax[0].legend()
    ax[1].legend()
    plt.savefig('JPM_macd.png')
    plt.clf()

    # momentum chart
    fig, ax = plt.subplots(2, 1)
    fmt_month = mdates.MonthLocator()
    p = ax[0].plot(df.index, ndf, color='blue')
    ax[0].set_title(f"{ticker} Stock Price vs Momentum")
    ax[0].set_ylabel("Normalized Prices")
    p[0].set_label('Stock Price')
    ax[0].xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    s = ax[1].plot(df.index, mom, color='red')
    u = ax[1].plot(df.index, [0.2] * len(df.index), color='black')
    l = ax[1].plot(df.index, [-0.2] * len(df.index), color='black')
    ax[1].xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    ax[1].set_ylabel("Momentum")
    s[0].set_label('Momentum (20 days)')
    plt.xlabel("Date")
    ax[0].legend()
    ax[1].legend()
    plt.savefig('JPM_mom.png')
    plt.clf()