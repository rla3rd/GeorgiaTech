import datetime as dt
import pandas as pd
import ManualStrategy as ms
import StrategyLearner as sl
from marketsimcode import compute_portvals
import experiment1 as ex1
import experiment2 as ex2
import random
import warnings
import subprocess
warnings.filterwarnings("ignore")


def author():
    return "ralbright7"


if __name__ == '__main__':
    # JPM, AAPL, UNH, ML4T-220, SINE_FAST_NOISE
    seed = random.seed(903548616)
    ticker = "JPM"

    start_dt = dt.datetime(2008, 1, 1)
    end_dt = dt.datetime(2009, 12, 31)
    start_value = 100000
    commission = 9.95
    impact = 0.005
    evidence = True

    # manual strategy in sample
    manual = ms.generate_strategy(
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)

    mdf = manual.pdf

    # manual strategy out of sample
    evidence = False
    start_dt = dt.datetime(2010, 1, 1)
    end_dt = dt.datetime(2011, 12, 31)

    ms.generate_strategy(
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)


    # strategy learner in sample
    start_dt = dt.datetime(2008, 1, 1)
    end_dt = dt.datetime(2009, 12, 31)
    evidence = True

    strat = sl.generate_strategy(
        None,
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)

    pdf = strat.pdf

    # benchmark in sample
    # this is only used for experiment 1 and 2
    # generate_strategy in ManualStrategy.py and StrategyLearner.py
    # generate this internally
    bench = {
        'Symbol': [ticker, ticker],
        'Date': [start_dt, strat.pdf.index[-1]],
        'Order': ['BUY', 'SELL'],
        'Shares': [1000, 1000]}

    bench = pd.DataFrame(bench, index=[start_dt, strat.pdf.index[-1]])
    bdf = compute_portvals(
        bench,
        start_val=start_value,
        commission=0,
        impact=0)

    bdf = bdf / bdf[0]

    # strategy learner out of sample
    evidence = False
    start_dt = dt.datetime(2010, 1, 1)
    end_dt = dt.datetime(2011, 12, 31)

    strat = sl.generate_strategy(
        strat,
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)

    # no assigment to pdf here because expirements
    # are done on in sample only

    ex1.generate_plots(ticker, pdf, mdf, bdf)

    # experiment 2 is no commissions or impact
    start_dt = dt.datetime(2008, 1, 1)
    end_dt = dt.datetime(2009, 12, 31)
    start_value = 100000
    commission = 0
    impact = 0
    # evidence in generate strategy controls add evidence
    # we dont want to train the q-learner any more so set it
    # to false
    evidence = False

    manual = ms.generate_strategy(
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)

    mdf = manual.pdf

    strat = sl.generate_strategy(
        strat,
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)

    pdf = strat.pdf

    ex2.generate_plots(ticker, pdf, mdf, bdf)
