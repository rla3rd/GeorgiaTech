import pandas as pd
import numpy as np
import datetime as dt
from util import get_data
import indicators as ind
from marketsimcode import compute_portvals
from marketsimcode import get_portfolio_stats
from matplotlib import pyplot as plt
import matplotlib.dates as mdates


def author():
    return "ralbright7"


class ManualStrategy():
    def __init__(self):
        pass

    def testPolicy(
        self,
        symbol="AAPL",
        sd=dt.datetime(2010, 1, 1),
        ed=dt.datetime(2011, 12, 31),
        sv=100000
    ):
        self.symbol = symbol
        self.sd = sd - dt.timedelta(days=365)
        self.ed = ed
        self.sv = sv

        df = get_data(
            [symbol],
            pd.date_range(self.sd, self.ed, freq='B'),
            addSPY=False)
        df = df.sort_index()
        # fwd fill then backfill
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)

        idx = df.index.to_series().between(sd, self.ed)
        self.data = df[idx].copy()
        sma = ind.sma(df, 50)
        self.data['sma'] = sma[idx].copy()
        ema = ind.ema(df, 10)
        self.data['ema'] = ema[idx].copy()
        bb = ind.bb_pct(df, 40, lvl=1, smooth=3)
        self.data['bb'] = bb[idx].copy()
        macd = ind.macd(df, 12, 26, 9)
        self.data['macd'] = macd[idx].copy()
        mom = ind.momentum(df, 3, smooth=1)
        self.data['mom'] = mom[idx].copy()

        # normalize prices
        self.data[f'n_{symbol}'] = (
            self.data[symbol] / self.data[symbol].iloc[0])
        self.data['n_sma'] = self.data['sma'] / self.data[symbol].iloc[0]
        self.data['n_ema'] = self.data['ema'] / self.data[symbol].iloc[0]
        self.data['cross'] = self.data['n_ema'] - self.data['n_sma']

        signals = np.zeros(self.data.shape[0])
        signals.fill(np.nan)
        rows = self.data.to_dict('records')
        for i in range(len(rows)):
            if i > 0:
                y = rows[i-1]
                t = rows[i]
                if len(signals[~np.isnan(signals)]) > 0:
                    last_signal = signals[~np.isnan(signals)][-1]
                else:
                    last_signal = 0

                long_avg = (
                    t['cross'] > 0
                    and y['cross'] <= 0
                    and last_signal != 1)
                short_avg = (
                    t['cross'] < 0
                    and y['cross'] >= 0
                    and last_signal != -1)
                long_bb = (
                    t['bb'] >= 0.8
                    and y['bb'] < 0.8
                    and last_signal != 1)
                short_bb = (
                    t['bb'] <= -0.8
                    and y['bb'] > -0.8
                    and last_signal != 1)
                long_macd = (
                    t['macd'] > 0
                    and y['macd'] <= 0
                    and last_signal != 1)
                short_macd = (
                    t['macd'] < 0
                    and y['macd'] >= 0
                    and last_signal != -1)
                long_mom = (
                    t['mom'] < 0
                    and y['mom'] >= 0
                    and last_signal != -1)
                short_mom = (
                    t['mom'] > 0
                    and y['mom'] <= 0
                    and last_signal != 1)

                if long_avg or long_bb or long_macd or long_mom:
                    signals[i] = 1
                if short_avg or short_bb or short_macd or short_mom:
                    signals[i] = -1

        self.data['signal'] = signals
        self.data['signal'].fillna(method='ffill', inplace=True)
        if pd.isnull(self.data['signal'].iloc[0]):
            self.data['signal'].iloc[0] = 0
        self.data['holdings'] = self.data['signal'] * 1000
        self.data['holdings'].fillna(method='ffill', inplace=True)

        #  back into trades by taking diff of holdings
        trades = self.data['holdings'].diff()
        trades.fillna(0, inplace=True)
        return trades

    def generate_orders(
        self,
        trades,
        symbol="AAPL",
        sd=dt.datetime(2010, 1, 1),
        ed=dt.datetime(2011, 12, 31)
    ):

        rng = pd.date_range(sd, ed, freq='B')
        sd = pd.Timestamp(rng[0].value)
        ed = pd.Timestamp(rng[-1].value)

        # we only want where the shares changes
        trades = trades[trades != 0]
        orders = trades.to_frame(name='Shares')
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

        if trades.iloc[-1] == 1000:
            action = 'SELL'
        else:
            action = 'BUY'

        # add a final order onto the dataframe to get to the last day
        orders = orders.append({
            'Symbol': symbol,
            'Order': action,
            'Shares': trades.iloc[-1],
            'Date': ed}, ignore_index=True)

        # sort orders then return
        orders.sort_values(by=['Date'], inplace=True)
        self.orders = orders
        return orders


def generate_strategy(
    ticker,
    start_dt,
    end_dt,
    start_value,
    commission,
    impact,
    evidence
):
    time_start = dt.datetime.now()

    if start_dt.year == 2008:
        sample = 'in-sample'
    else:
        sample = 'out-of-sample'

    rng = pd.date_range(start_dt, end_dt, freq='B')
    start_dt = pd.Timestamp(rng[0].value)
    end_dt = pd.Timestamp(rng[-1].value)

    strategy = ManualStrategy()
    tdf = strategy.testPolicy(
        symbol=ticker,
        sd=start_dt,
        ed=end_dt,
        sv=start_value)

    odf = strategy.generate_orders(
        tdf,
        symbol=ticker,
        sd=start_dt,
        ed=end_dt)

    pdf = compute_portvals(
        odf,
        start_val=start_value,
        commission=commission,
        impact=impact)

    if tdf.iloc[-1] == 1000:
        action = 'SELL'
    else:
        action = 'BUY'

    bench = {
        'Symbol': [ticker, ticker],
        'Date': [start_dt, end_dt],
        'Order': ['BUY', action],
        'Shares': [1000, 1000]}
 
    bench = pd.DataFrame(bench, index=[start_dt, end_dt])
    bdf = compute_portvals(
        bench,
        start_val=start_value,
        commission=0,
        impact=0)

    pdf = pdf / pdf[0]
    bdf = bdf / bdf[0]

    strategy.pdf = pdf

    x = bdf.index
    x_b = pdf[
        pdf.index.isin(
            odf[
                (odf['Order'] == 'BUY')
                & odf['Shares'] > 0]['Date'])].index
    x_s = pdf[
        pdf.index.isin(
            odf[
                (odf['Order'] == 'SELL')
                & odf['Shares'] > 0]['Date'])].index
    fig, ax = plt.subplots()
    # fmt_month = mdates.MonthLocator()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    bch = plt.plot(x, bdf, color='green')
    bch[0].set_label('benchmark')
    for xs in x_b:
        buys = plt.axvline(x=xs, color='blue', alpha=0.4)
    buys.set_label('buys')
    opt = plt.plot(x, pdf, color='red')
    opt[0].set_label('manual strategy')
    for xs in x_s:
        sells = plt.axvline(x=xs, color='black', alpha=8.4)
    sells.set_label('sells')
    
    plt.title(f"{ticker} manual strategy ({sample}) vs benchmark")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.savefig(f'{ticker}_manual_{sample}_{commission}_{impact}.png')
    plt.clf()

    (
        bch_cum_ret,
        bch_avg_daily_ret,
        bch_std_daily_ret,
        bch_sharpe_ratio) = get_portfolio_stats(bdf)

    (
        opt_cum_ret,
        opt_avg_daily_ret,
        opt_std_daily_ret,
        opt_sharpe_ratio) = get_portfolio_stats(pdf)

    opt_stats = open(f'{ticker}_manual_strategy_{sample}_{commission}_{impact}_results.txt', 'w')
    opt_stats.write(f"Date Range: {start_dt} to {end_dt}\n")
    opt_stats.write("\n")
    opt_stats.write(f"bench cumulative return: {round(bch_cum_ret, 4)}\n")
    opt_stats.write(f"bench avg daily return: {round(bch_avg_daily_ret, 4)}\n")
    opt_stats.write(
        f"bench stddev daily return: {round(bch_std_daily_ret, 4)}\n")
    opt_stats.write(f"bench sharpe ratio: {round(bch_sharpe_ratio, 4)}\n")
    opt_stats.write(
        f"bench final port value: {round(bdf[-1] * start_value, 2)}\n")
    opt_stats.write("\n")
    opt_stats.write(
        f"man strat cumulative return: {round(opt_cum_ret, 4)}\n")
    opt_stats.write(
        f"man strat avg daily return: {round(opt_avg_daily_ret, 4)}\n")
    opt_stats.write(
        f"man strat stddev daily return: {round(opt_std_daily_ret, 4)}\n")
    opt_stats.write(
        f"man strat sharpe ratio: {round(opt_sharpe_ratio, 4)}\n")
    opt_stats.write(
        f"man strat final port value: {round(pdf[-1] * start_value, 2)}\n")

    opt_stats.flush()
    opt_stats.close()

    time_end = dt.datetime.now()
    print(f"Manual Strategy {sample} Elapsed: {time_end - time_start}")
    return strategy


if __name__ == '__main__':
    # JPM, AAPL, UNH, ML4T-220, SINE_FAST_NOISE
    ticker = "JPM"
    start_dt = dt.datetime(2008, 1, 1)
    end_dt = dt.datetime(2009, 12, 31)
    start_value = 100000
    commission = 9.95
    impact = 0.005
    evidence = True

    generate_strategy(
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)

    evidence = False
    start_dt = dt.datetime(2010, 1, 1)
    end_dt = dt.datetime(2011, 12, 31)

    generate_strategy(
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)
