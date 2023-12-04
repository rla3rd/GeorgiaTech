""""""  		  	   		   	 		  		  		    	 		 		   		 		  
"""  		  	   		   	 		  		  		    	 		 		   		 		  
Template for implementing StrategyLearner  (c) 2016 Tucker Balch  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
Copyright 2018, Georgia Institute of Technology (Georgia Tech)  		  	   		   	 		  		  		    	 		 		   		 		  
Atlanta, Georgia 30332  		  	   		   	 		  		  		    	 		 		   		 		  
All Rights Reserved  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
Template code for CS 4646/7646  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
Georgia Tech asserts copyright ownership of this template and all derivative  		  	   		   	 		  		  		    	 		 		   		 		  
works, including solutions to the projects assigned in this course. Students  		  	   		   	 		  		  		    	 		 		   		 		  
and other users of this template code are advised not to share it with others  		  	   		   	 		  		  		    	 		 		   		 		  
or to make it available on publicly viewable websites including repositories  		  	   		   	 		  		  		    	 		 		   		 		  
such as github and gitlab.  This copyright statement should not be removed  		  	   		   	 		  		  		    	 		 		   		 		  
or edited.  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
We do grant permission to share solutions privately with non-students such  		  	   		   	 		  		  		    	 		 		   		 		  
as potential employers. However, sharing with other current or future  		  	   		   	 		  		  		    	 		 		   		 		  
students of CS 7646 is prohibited and subject to being investigated as a  		  	   		   	 		  		  		    	 		 		   		 		  
GT honor code violation.  		  	   		   	 		  		  		    	 		 		   		 		  
  		  	   		   	 		  		  		    	 		 		   		 		  
-----do not edit anything above this line---  		  	   		   	 		  		  		    	 		 		   		 		  

Student Name: Richard Albright (replace with your name)
GT User ID: ralbright7 (replace with your User ID)
GT ID: 903548616 (replace with your GT ID)
"""

import datetime as dt
import random
import pandas as pd
import numpy as np
from pandas.io.formats.format import Datetime64Formatter
from util import get_data
import indicators as ind
from marketsimcode import compute_portvals
from marketsimcode import get_portfolio_stats
import QLearner as ql
from matplotlib import pyplot as plt
import matplotlib.dates as mdates


class StrategyLearner(object):
    """
    A strategy learner that can learn a trading policy using the
    same indicators used in ManualStrategy.

    :param verbose: If “verbose” is True, your code can print out 
        information for debugging.
        If verbose = False your code should not generate ANY output.
    :type verbose: bool
    :param impact: The market impact of each transaction, defaults to 0.0
    :type impact: float
    :param commission: The commission amount charged, defaults to 0.0
    :type commission: float
    """
    # constructor
    def __init__(self, verbose=False, impact=0.0, commission=0.0):
        """
        Constructor method
        """
        self.verbose = verbose
        self.impact = impact
        self.commission = commission
        self.bin_size = 2
        self.bins = {}
        self.num_actions = 3
        self.converge_ct = 0
        self.converged = False
        self.epochs = 1000
        self.indicators = ['cross', 'bb', 'macd', 'mom']
        self.sma_days = 50
        self.ema_days = 10
        self.bb_days = 40
        self.bb_smooth = 3
        self.bb_lvl = 1
        self.macd_fast = 12
        self.macd_slow = 26
        self.macd_signal = 9
        self.mom_days = 3
        self.mom_smooth = 1

    def author(self):
        return "ralbright7"

    def returns_converged(self, prior_return, current_return):
        if abs(current_return - prior_return) <= 0.001:
            self.converge_ct += 1
        else:
            if self.converge_ct > 0:
                self.converge_ct -= 1
        if self.converge_ct > 3:
            self.converged = True

    def get_holdings_reward(self, holdings, ret, action):
        reward = 0
        # 0 = short, 1 = hold, 2 = long
        if holdings == 1000:
            if action == 0:
                holdings -= 2000
                reward = -ret + self.impact
            elif action == 1:
                reward = ret
            elif action == 2:
                reward = 0
        elif holdings == 0:
            if action == 0:
                holdings -= 1000
                reward = -ret
            elif action == 1:
                reward = 0
            elif action == 2:
                holdings += 1000
                reward = ret
        elif holdings == -1000:
            if action == 0:
                reward = 0
            elif action == 1:
                reward = -ret
            elif action == 2:
                holdings += 2000
                reward = ret - self.impact
        return holdings, reward

    def indicators_state(self, indicators, idx):
        base = 1
        state = 0
        for indicator in indicators:
            curr_state = np.digitize(
                self.data[indicator].iloc[idx],
                self.bins[indicator], right=True)
            state = curr_state * base + state
            base *= 10
        return state

    # this method should create a QLearner, and train it for trading
    def add_evidence(
        self,
        symbol="IBM",
        sd=dt.datetime(2008, 1, 1),
        ed=dt.datetime(2009, 12, 31),
        sv=100000,
    ):
        """
        Trains your strategy learner over a given time frame.

        :param symbol: The stock symbol to train on
        :type symbol: str
        :param sd: A datetime object that represents the start date,
            defaults to 1/1/2008
        :type sd: datetime
        :param ed: A datetime object that represents the end date,
            defaults to 1/1/2009
        :type ed: datetime
        :param sv: The starting value of the portfolio
        :type sv: int
        """

        # add your code to do learning here
        self.symbol = symbol
        self.sd = sd - dt.timedelta(days=365)
        self.ed = ed
        self.sv = sv

        dates = pd.date_range(self.sd, self.ed)

        df = get_data(
            [symbol],
            dates)

        df = df.sort_index()
        df = df[[symbol]].copy()

        # fwd fill then backfill
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)

        m, n = df.shape

        idx = df.index.to_series().between(sd, self.ed)
        self.data = df[idx].copy()
        sma = ind.sma(
            df,
            self.sma_days)
        self.data['sma'] = sma[idx].copy()
        ema = ind.ema(
            df,
            self.ema_days)
        self.data['ema'] = ema[idx].copy()
        bb = ind.bb_pct(
            df,
            self.bb_days,
            smooth=self.bb_smooth,
            lvl=self.bb_lvl)
        self.data['bb'] = bb[idx].copy()
        macd = ind.macd(
            df,
            self.macd_fast,
            self.macd_slow,
            self.macd_signal)
        self.data['macd'] = macd[idx].copy()
        mom = ind.momentum(
            df,
            self.mom_days,
            smooth=self.mom_smooth)
        self.data['mom'] = mom[idx].copy()

        # normalize prices
        self.data[f'n_{symbol}'] = (
            self.data[symbol] / self.data[symbol].iloc[0])
        self.data['n_sma'] = self.data['sma'] / self.data[symbol].iloc[0]
        self.data['n_ema'] = self.data['ema'] / self.data[symbol].iloc[0]
        self.data['cross'] = self.data['n_ema'] - self.data['n_sma']

        # get tomorrows daily returns for rewards
        self.data['returns'] = self.data[f'n_{symbol}'].diff().shift(-1)
        self.data['returns'].iloc[-1] = 0

        # get each indicator's quartiles
        for indicator in self.indicators:
            self.bins[indicator] = pd.qcut(
                self.data[indicator].values,
                self.bin_size,
                labels=False,
                retbins=True)[1]

            # remove min and max values
            self.bins[indicator] = self.bins[indicator][1:-1]

        self.learner = ql.QLearner(
            # max number of states using median bins with 4 indicators is 1112
            num_states=1112, # int(f"1{''.join(['0'] * len(self.indicators))}"),
            num_actions=self.num_actions,
            alpha=0.2,
            gamma=0.9,
            rar=0.3,
            radr=0.9,
            dyna=0,
            verbose=self.verbose)

        epoch = 0
        prior_return = 0
        current_return = None

        while not self.converged and epoch < self.epochs:

            self.data['holdings'] = np.nan
            self.data['holdings'].iloc[0] = 0
            state = self.indicators_state(self.indicators, 0)
            action = self.learner.querysetstate(state)
            self.data['holdings'].iloc[0], reward = self.get_holdings_reward(
                self.data['holdings'].iloc[0],
                self.data['returns'].iloc[0],
                action)

            for i in range(1, self.data.shape[0]):
                state = self.indicators_state(self.indicators, i)
                action = self.learner.query(state, reward)
                self.data[
                    'holdings'].iloc[i], reward = self.get_holdings_reward(
                    self.data['holdings'].iloc[i-1],
                    self.data['returns'].iloc[i],
                    action)

                # print(epoch, state, action, self.data['holdings'].iloc[i],
                # reward, current_return)

            self.data['holdings'].iloc[-1] = 0
            self.data['holdings'].ffill(inplace=True)
            self.data['holdings'].fillna(0, inplace=True)

            #  back into trades by taking diff of holdings
            trades = self.data['holdings'].diff()

            # we only want where the shares changes
            trades = trades[trades != 0]
            orders = trades.to_frame(name='Shares')
            orders.index.name = 'Date'
            orders.reset_index(inplace=True)
            orders['Symbol'] = symbol
            orders['Order'] = 'buy'
            sell_idx = orders['Shares'] < 0
            orders.loc[sell_idx, ['Order']] = 'sell'
            orders['Shares'] = np.abs(orders['Shares'])

            # add a buy of 0 shares onto the dataframe to get to the 1st day
            orders = orders.append({
                'Symbol': symbol,
                'Order': 'buy',
                'Shares': 0,
                'Date': sd}, ignore_index=True)

            # add a buy of 0 shares onto the dataframe to get to the last day
            orders = orders.append({
                'Symbol': symbol,
                'Order': 'buy',
                'Shares': 0,
                'Date': ed}, ignore_index=True)

            pdf = compute_portvals(
                orders,
                start_val=sv,
                commission=self.commission,
                impact=self.impact)

            pdf = pdf / pdf[0]
            current_return = pdf.iloc[-1] - 1
            self.returns_converged(prior_return, current_return)
            if self.verbose:
                print(epoch, prior_return, current_return, self.converge_ct)
            epoch += 1
            prior_return = current_return

        return orders

    # this method should use the existing policy and test it against new data
    def testPolicy(
        self,
        symbol="IBM",
        sd=dt.datetime(2009, 1, 1),
        ed=dt.datetime(2010, 1, 1),
        sv=10000,
    ):
        """
        Tests your learner using data outside of the training data

        :param symbol: The stock symbol that you trained on on
        :type symbol: str
        :param sd: A datetime object that represents the start date,
            defaults to 1/1/2008
        :type sd: datetime
        :param ed: A datetime object that represents the end date,
            defaults to 1/1/2009
        :type ed: datetime
        :param sv: The starting value of the portfolio
        :type sv: int
        :return: A DataFrame with values representing trades for each day.
            Legal values are +1000.0 indicating a buy of 1000 shares,
            -1000.0 indicating a sell of 1000 shares, and 0.0 indicating
            NOTHING. Values of +2000 and -2000 for trades are also legal
            when switching from long to short or short to long so long
            as net holdings are constrained to -1000, 0, and 1000.
        :rtype: pandas.DataFrame
        """

        # add your code to do learning here
        self.symbol = symbol
        self.sd = sd - dt.timedelta(days=365)
        self.ed = ed
        self.sv = sv

        dates = pd.date_range(self.sd, self.ed)
        df = get_data(
            [symbol],
            dates)

        df = df.sort_index()
        df = df[[symbol]].copy()

        # fwd fill then backfill
        df.fillna(method='ffill', inplace=True)
        df.fillna(method='bfill', inplace=True)

        m, n = df.shape

        idx = df.index.to_series().between(sd, self.ed)
        self.outdata = df[idx].copy()
        sma = ind.sma(
            df,
            self.sma_days)
        self.outdata['sma'] = sma[idx].copy()
        ema = ind.ema(
            df,
            self.ema_days)
        self.outdata['ema'] = ema[idx].copy()
        bb = ind.bb_pct(
            df,
            self.bb_days,
            smooth=self.bb_smooth,
            lvl=self.bb_lvl)
        self.outdata['bb'] = bb[idx].copy()
        macd = ind.macd(
            df,
            self.macd_fast,
            self.macd_slow,
            self.macd_signal)
        self.outdata['macd'] = macd[idx].copy()
        mom = ind.momentum(
            df,
            self.mom_days,
            smooth=self.mom_smooth)
        self.outdata['mom'] = mom[idx].copy()

        # normalize prices
        self.outdata[f'n_{symbol}'] = (
            self.outdata[symbol] / self.outdata[symbol].iloc[0])
        self.outdata['n_sma'] = (
            self.outdata['sma'] / self.outdata[symbol].iloc[0])
        self.outdata['n_ema'] = (
            self.outdata['ema'] / self.outdata[symbol].iloc[0])
        self.outdata['cross'] = self.outdata['n_ema'] - self.outdata['n_sma']

        self.outdata['holdings'] = np.nan
        self.outdata['holdings'].iloc[0] = 0

        for i in range(1, self.outdata.shape[0]):
            state = self.indicators_state(self.indicators, i)
            action = self.learner.querysetstate(state)
            self.outdata['holdings'].iloc[i], _ = self.get_holdings_reward(
                self.outdata['holdings'].iloc[i-1],
                0,
                action)

        self.outdata['holdings'].iloc[-1] = 0
        self.outdata['holdings'].ffill(inplace=True)

        #  back into trades by taking diff of holdings
        trades = self.outdata[['holdings']].diff()
        trades.fillna(0, inplace=True)
        trades = trades.rename(columns={"holdings": "Shares"})
        return trades

    def generate_orders(
        self,
        trades,
        symbol="AAPL",
        sd=dt.datetime(2010, 1, 1),
        ed=dt.datetime(2011, 12, 31)
    ):
        # we only want where the shares changes
        orders = trades[trades['Shares'] != 0]
        # orders = trades.to_frame(name='Shares')
        orders.index.name = 'Date'
        orders.reset_index(inplace=True)
        orders['Symbol'] = symbol
        orders['Order'] = 'buy'
        sell_idx = orders['Shares'] < 0
        orders.loc[sell_idx, ['Order']] = 'sell'
        orders['Shares'] = np.abs(orders['Shares'])

        # add a buy of 0 shares onto the dataframe to get to the 1st day
        orders = orders.append({
            'Symbol': symbol,
            'Order': 'buy',
            'Shares': 0,
            'Date': sd}, ignore_index=True)

        if trades.iloc[-1]['Shares'] == 1000:
            action = 'sell'
        else:
            action = 'buy'

        # add a final order onto the dataframe to get to the last day
        orders = orders.append({
            'Symbol': symbol,
            'Order': action,
            'Shares': trades.iloc[-1]['Shares'],
            'Date': ed}, ignore_index=True)

        # sort orders then return
        orders.sort_values(by=['Date'], inplace=True)
        self.orders = orders
        return orders


def generate_strategy(
    strategy,
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

    if evidence:
        strategy = StrategyLearner()

        tdf = strategy.add_evidence(
            symbol=ticker,
            sd=start_dt,
            ed=end_dt,
            sv=start_value)

    rng = pd.date_range(start_dt, end_dt, freq='B')
    start_dt = rng[0]
    end_dt = rng[-1]

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

    if tdf.iloc[-1]['Shares'] == 1000:
        action = 'sell'
    else:
        action = 'buy'

    bench = {
        'Symbol': [ticker, ticker],
        'Date': [start_dt, end_dt],
        'Order': ['buy', action],
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
    strategy.bdf = bdf

    x = pdf.index
    x_b = pdf[
        pdf.index.isin(
            odf[
                (odf['Order'] == 'buy')
                & odf['Shares'] > 0]['Date'])].index
    x_s = pdf[
        pdf.index.isin(
            odf[
                (odf['Order'] == 'sell')
                & odf['Shares'] > 0]['Date'])].index
    fig, ax = plt.subplots()
    # fmt_month = mdates.MonthLocator()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
    bch = plt.plot(x, bdf, color='green')
    bch[0].set_label('benchmark')
    for xs in x_b:
        buys = plt.axvline(x=xs, color='blue', alpha=0.4)
    buys.set_label('buys')
    x = pdf.index
    opt = plt.plot(x, pdf, color='red')
    opt[0].set_label('strategy learner')
    for xs in x_s:
        sells = plt.axvline(x=xs, color='black', alpha=8.4)
    sells.set_label('sells')
    plt.title(f"Q-learner {ticker} vs benchmark (${commission} - {impact * 100}%)")
    plt.xlabel("Date")
    plt.ylabel("Portfolio Value")
    plt.legend()
    plt.savefig(f'{ticker}_Q-learner_{sample}_{commission}_{impact}.png')
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

    opt_stats = open(f'{ticker}_Q-learner_{sample}_{commission}_{impact}_results.txt', 'w')
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
        f"learner cumulative return: {round(opt_cum_ret, 4)}\n")
    opt_stats.write(
        f"learner avg daily return: {round(opt_avg_daily_ret, 4)}\n")
    opt_stats.write(
        f"learner stddev daily return: {round(opt_std_daily_ret, 4)}\n")
    opt_stats.write(
        f"learner sharpe ratio: {round(opt_sharpe_ratio, 4)}\n")
    opt_stats.write(
        f"learner final port value: {round(pdf[-1] * start_value, 2)}\n")

    opt_stats.flush()
    opt_stats.close()
    time_end = dt.datetime.now()
    print(f"Q-learner {sample} Elapsed: {time_end - time_start}")
    return strategy


if __name__ == "__main__":
    # JPM, AAPL, UNH, ML4T-220, SINE_FAST_NOISE
    random.seed(903548616)
    ticker = "JPM"
    start_dt = dt.datetime(2008, 1, 1)
    end_dt = dt.datetime(2009, 12, 31)
    start_value = 100000
    commission = 0
    impact = 0
    evidence = True

    strat = generate_strategy(
        None,
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

    strat = generate_strategy(
        strat,
        ticker,
        start_dt,
        end_dt,
        start_value,
        commission,
        impact,
        evidence)
