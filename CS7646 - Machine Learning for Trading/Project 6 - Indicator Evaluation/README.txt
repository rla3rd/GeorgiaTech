TheoreticallyOptimalStrategy.py

This file generates the optimal portfolio strategy base on future price knowledge.
It implements the testPolicy function
This file is not run on its own.


marketsimcode.py

This file includes a modified market simulator that takes a trades dataframe as input
This file is not run on its own.


testproject.py

This file calls the testPolicy function to generate trades for input into the market simulator.


execution of testproject.py
PYTHONPATH=../:. python testproject.py

generates:
optimal_portfolio.png 
p6_results.txt

indicators.py

This file executes the following indicators and plots them
50 day simple moving average
5 day exponential moving average
50 day bollinger band percent using 5 day exponential moving average
macd using a default of fast 12 day ema, slow 26 day ema, 9 day ema signal
20 day momentum using a 5 day exponential moving average

execution of indicators
PYTHONPATH=../:. python indicator.py

generates:
JPM_sma.png
JPM_ema.png
JPM_bollinger.png
JPM_macd.png
JPM_mom.png

