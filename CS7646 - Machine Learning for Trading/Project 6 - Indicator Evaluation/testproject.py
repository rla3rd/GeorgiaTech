import TheoreticallyOptimalStrategy as tos
from marketsimcode import compute_portvals
from marketsimcode import get_portfolio_stats
import datetime as dt
import pandas as pd
from matplotlib import pyplot as plt
import matplotlib.dates as mdates
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


def author(self):
    return "ralbright7"


ticker = "JPM"
begin_date = dt.datetime(2008, 1, 1)
end_date = dt.datetime(2009, 12, 31)
init_port_value = 100000

tdf = tos.testPolicy(
    symbol=ticker,
    sd=begin_date,
    ed=end_date,
    sv=init_port_value)

pdf = compute_portvals(tdf, start_val=init_port_value, commission=0, impact=0)

bench = {
    'Symbol': [ticker, ticker],
    'Date': [begin_date, end_date],
    'Order': ['BUY', 'BUY'],
    'Shares': [1000, 0]}

benchmark = pd.DataFrame(bench, index=[begin_date, end_date])
bdf = compute_portvals(
    benchmark,
    start_val=init_port_value,
    commission=0,
    impact=0)

pdf = pdf / pdf[0]
bdf = bdf / bdf[0]

x = pdf.index
fig, ax = plt.subplots()
fmt_month = mdates.MonthLocator()
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b-%y'))
bch = plt.plot(x, bdf, color='green')
bch[0].set_label('Benchmark')
opt = plt.plot(x, pdf, color='red')
opt[0].set_label('Optimal Portfolio')
plt.title("Optimal Porfolio Value Vs Benchmark")
plt.xlabel("Date")
plt.ylabel("Portfolio Value")
plt.legend()
plt.savefig('optimal_portfolio.png')
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

opt_stats = open('p6_results.txt', 'w')
opt_stats.write(f"Date Range: {begin_date} to {end_date}\n")
opt_stats.write("\n")
opt_stats.write(f"benchmark cumulative return: {round(bch_cum_ret, 4)}\n")
opt_stats.write(f"benchmark avg daily return: {round(bch_avg_daily_ret, 4)}\n")
opt_stats.write(
    f"benchmark stddev daily return: {round(bch_std_daily_ret, 4)}\n")
opt_stats.write(f"benchmark sharpe ratio: {round(bch_sharpe_ratio, 4)}\n")
opt_stats.write(
    f"benchmark final port value: {round(bdf[-1] * init_port_value, 2)}\n")
opt_stats.write("\n")
opt_stats.write(f"optimal cumulative return: {round(opt_cum_ret, 4)}\n")
opt_stats.write(f"optimal avg daily return: {round(opt_avg_daily_ret, 4)}\n")
opt_stats.write(
    f"optimal stddev daily return: {round(opt_std_daily_ret, 4)}\n")
opt_stats.write(f"optimal sharpe ratio: {round(opt_sharpe_ratio, 4)}\n")
opt_stats.write(
    f"optimal final port value: {round(pdf[-1] * init_port_value, 2)}\n")

opt_stats.flush()
opt_stats.close()
