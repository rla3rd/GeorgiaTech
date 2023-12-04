import random
import datetime as dt
import pandas as pd
import ManualStrategy as ms
import StrategyLearner as sl
from marketsimcode import compute_portvals
from marketsimcode import get_portfolio_stats
from matplotlib import pyplot as plt
import matplotlib.dates as mdates


def author():
    return "ralbright7"


def run_experiment(ticker):
    time_start = dt.datetime.now()
    start_dt = dt.datetime(2008, 1, 1)
    end_dt = dt.datetime(2009, 12, 31)
    start_value = 100000
    commission = 9.95
    impact = 0.005

    rng = pd.date_range(start_dt, end_dt, freq='B')
    start_dt = rng[0]
    end_dt = rng[-1]

    strategy = sl.StrategyLearner()

    stdf = strategy.add_evidence(
        symbol=ticker,
        sd=start_dt,
        ed=end_dt,
        sv=start_value)

    stdf = strategy.testPolicy(
        symbol=ticker,
        sd=start_dt,
        ed=end_dt,
        sv=start_value)

    sodf = strategy.generate_orders(
        stdf,
        symbol=ticker,
        sd=start_dt,
        ed=end_dt)

    spdf = compute_portvals(
        sodf,
        start_val=start_value,
        commission=commission,
        impact=impact)

    if stdf.iloc[-1]['Shares'] == 1000:
        action = 'SELL'
    else:
        action = 'BUY'

    bench = {
        'Symbol': [ticker, ticker],
        'Date': [start_dt, end_dt],
        'Order': ['BUY', action],
        'Shares': [1000, 1000]}

    manual = ms.ManualStrategy()

    mtdf = manual.testPolicy(
        symbol=ticker,
        sd=start_dt,
        ed=end_dt,
        sv=start_value)

    modf = manual.generate_orders(
        mtdf,
        symbol=ticker,
        sd=start_dt,
        ed=end_dt)

    mpdf = compute_portvals(
        modf,
        start_val=start_value,
        commission=commission,
        impact=impact)

    bench = pd.DataFrame(bench, index=[start_dt, end_dt])
    bdf = compute_portvals(
        bench,
        start_val=start_value,
        commission=0,
        impact=0)

    mpdf = mpdf / mpdf[0]
    spdf = spdf / spdf[0]
    bdf = bdf / bdf[0]
    generate_plots(ticker, spdf, mpdf, bdf)
    time_end = dt.datetime.now()
    print(f'Ex 1 Elapsed: {time_end - time_start}')


def generate_plots(ticker, spdf, mpdf, bdf):
    x = bdf.index
    _, ax = plt.subplots()
    mdates.MonthLocator()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    bch = plt.plot(x, bdf, color='green')
    bch[0].set_label('benchmark')
    opt = plt.plot(x, mpdf, color='red')
    opt[0].set_label('manual strategy')
    sopt = plt.plot(x, spdf, color='blue')
    sopt[0].set_label('strategy learner')
    plt.title(f"{ticker} manual vs Q-learner vs benchmark ($9.95 - 0.5%)")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.savefig(f'{ticker}_experiment_1.png')
    plt.clf()


if __name__ == '__main__':
    #random.seed(903548616)
    ticker = "JPM"
    run_experiment(ticker)
