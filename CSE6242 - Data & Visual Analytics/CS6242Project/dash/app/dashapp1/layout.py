import pandas as pd
from pandas.tseries.offsets import DateOffset
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import dash_table


# slider setup
maxmarks = 13
tday = pd.Timestamp(2018, 12, 31)
y1date = tday+DateOffset(years=-maxmarks+1)
datelist = pd.date_range(y1date, periods=maxmarks, freq='Y')
dlist = pd.DatetimeIndex(datelist).normalize()
tags = {}
datevalues = {}
x = 1
for i in dlist:
    tags[x] = (i + DateOffset(years=1)).strftime('%Y')
    datevalues[x] = i
    x = x + 1


# tooltip
def tooltip(target, text):
    return html.Span(
        [
            html.Span(
                "?",
                id=target,
                style={
                    "textAlign": "center",
                    "color": "black",
                },
                className="dot"),
            dbc.Tooltip(
                text,
                target=target)
        ])


# header
# contains the username, page title, and logout button
header = html.Div(
    className="header",
    children=html.Div(
        className='container-width',
        style={'height': '100%'},
        children=[
            html.Div([
                html.Div([
                    html.H5(id='username'),
                    html.Div(id='userid', style={'display': 'none'})],
                    className="two columns row main-title"),
                html.Div([
                    html.H5(
                        "Portfolio Dashboard",
                        style={"background": "#ffffff"})],
                    className="nine columns row center-aligned"),
                html.Div([
                    html.A(
                        html.Button(
                            "Logout",
                            id='logout',
                            style={"background": "#ffffff"}),
                        href="/logout", className="right-aligned")],
                    className="one columns row")],
            ),
        ]
    )
)


# page body function
def serve_layout():
    return html.Div(
        [
            # header row
            header,
            # body
            html.Div([
                html.Div([
                    # row 1
                    html.Div([
                        # alerts
                        dbc.Alert(
                            id="ticker_alert",
                            is_open=False,
                            dismissable=True,
                            color="warning"),
                        dbc.Alert(
                            id="side_alert",
                            is_open=False,
                            color="warning"),
                        dbc.Alert(
                            id="value_alert",
                            is_open=False,
                            color="warning"),
                        dbc.Alert(
                            id="rewind_alert",
                            is_open=False,
                            dismissable=True,
                            color="warning"),
                        ],
                        className="twelve columns row alert-warning"),

                    # row 2
                    html.Div([
                        html.Div(
                            [
                                # date year slider
                                html.Div(
                                    [
                                        html.Span('Simulation Slider: '),
                                        tooltip(
                                            "slider-tooltip",
                                            """
                                            Use the slider to easily change
                                            years in the trade date control
                                            """)
                                    ],
                                    className="two columns"),
                                html.Div([
                                    dcc.Slider(
                                        id="dateslider",
                                        updatemode='mouseup',
                                        min=1,
                                        max=maxmarks,
                                        step=1,
                                        value=maxmarks-13,
                                        marks=tags),
                                    html.Div(
                                        id='slider-container',
                                        style={'margin-top': 30})
                                    ],
                                    className="ten columns")
                            ],
                            className="row")
                        ]),
                    # row 3
                    html.Div([
                        # date picker
                        html.Div([
                            html.Div(
                                [
                                    html.Span('Trade Date: '),
                                    tooltip(
                                        "datepicker-tooltip",
                                        """
                                        Choose a trade date.  The minimum
                                        date allowed is the date of the
                                        last position update.
                                        """)
                                ]),
                            dcc.DatePickerSingle(
                                id='datepicker')],
                            className="two columns row"),
                        # side dropdown
                        html.Div([
                            html.Div(
                                [
                                    html.Span('Buy/Sell: '),
                                    tooltip(
                                        "side-tooltip",
                                        """
                                        Choose a side.  You must have cash
                                        in the portfolio before you can
                                        purchase any stocks.
                                        """)
                                ]),
                            dcc.Dropdown(
                                id='side',
                                options=[
                                    {'label': 'BUY', 'value': 'B'},
                                    {'label': 'SELL', 'value': 'S'}
                                ],
                                value='B')],
                            className="two columns row"),
                        # ticker dropdown
                        html.Div([
                            html.Div(
                                [
                                    html.Span('Ticker: '),
                                    tooltip(
                                        "ticker-tooltip",
                                        """
                                        Choose a Ticker.  Pick cash if there
                                        is no money in the account.
                                        """),
                                    html.Span("PLEASE CREATE A CASH BALANCE PRIOR TO ADDING POSITIONS", 
                                        style={
                                            'fontWeight': 'bold',
                                            'textAlign': 'center'})
                                ]),
                            dcc.Dropdown(
                                id='ticker',
                                value=0)
                            ],
                            className="four columns row"),
                        # dollar value input box
                        html.Div([
                            html.Div(
                                [
                                    html.Span('Dollar Value: '),
                                    tooltip(
                                        "value-tooltip",
                                        """
                                        Choose a dollar amount
                                        to buy or sell.
                                        """)
                                ]),
                            dcc.Input(
                                id='value',
                                placeholder='Enter a value...',
                                type='number',
                                min=0,
                                value=10000)
                            ],
                            className="two columns row"),
                        # submit button
                        html.Div([
                            html.Div(
                                [
                                    html.Span('Execute: '),
                                    tooltip(
                                        "submit-tooltip",
                                        """
                                        Submit your order.
                                        """)
                                ]),
                            html.Button(
                                "Submit",
                                id='submit',
                                type="submit",
                                className="input button-primary")],
                            className="two columns")
                        ],
                        className="twelve columns row"),
                    # row 4
                    html.Div([
                        html.Div([
                            # screener table
                            html.Div([
                                    html.Span("Ticker Screener: "),
                                    tooltip(
                                        "screener-tooltip",
                                        """
                                        This is screening data for the ticker
                                        displayed in the dropdown select box.
                                        It is as of the date displayed in the
                                        table. With the exception of Beta, All
                                        metrics are calculated using a 1-Yr
                                        lookback of daily returns. Beta uses
                                        a 3-Yr lookback.
                                        """)
                                ],
                                className="h6 subtitle padded"),
                            dash_table.DataTable(
                                id='screener',
                                style_header={
                                    'fontWeight': 'bold',
                                    'backgroundColor': 'rgb(230, 230, 230)'},
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'Metric'},
                                        'fontWeight': 'bold',
                                        'textAlign': 'left'
                                    },
                                    {
                                        'if': {'column_id': 'Value'},
                                        'textAlign': 'left'
                                    },
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(248, 248, 248)'
                                    }],
                                style_as_list_view=True)],
                                className='two columns row'),

                            # stock chart
                            html.Div(
                                [
                                    html.Div(
                                        [
                                            html.Span(
                                                "Dropdown Ticker History: "),
                                            tooltip(
                                                "stock-tooltip",
                                                """
                                                This is a chart of the stock
                                                price history of the ticker
                                                displayed in the dropdown
                                                select box. It is as of the
                                                date selected in the trade
                                                date box. Beta and Volatility
                                                are also available through
                                                the legend control.  The other
                                                ratios are not available in
                                                this chart because they can
                                                have negative values and this
                                                chart is log scaled.
                                                """)
                                        ],
                                        className="h5 subtitle padded"),
                                    dcc.Graph(id='stock')
                                ],
                                className="eight columns row"),

                            # transactions table
                            html.Div([
                                html.Div([
                                    html.Span("Transactions: "),
                                    tooltip(
                                        "transactions-tooltip",
                                        """
                                        This is your transaction history. It
                                        allows rewinding of actions by
                                        selecting a point in time of your
                                        transaction history.  It will remove
                                        the transaction selected and all
                                        transactions following it. Select
                                        your point in time and click the
                                        Rewind button to undo transactions.
                                        """)],
                                    className="subtitle padded"),

                                html.Div([
                                    dash_table.DataTable(
                                        id='transactions',
                                        selected_rows=[],
                                        style_header={
                                            'fontWeight': 'bold',
                                            'textAlign': 'left',
                                            'backgroundColor': 'rgb(230, 230, 230)'},
                                        style_cell_conditional=[
                                            {

                                                'if': {'row_index': 'odd'},
                                                'backgroundColor': 'rgb(248, 248, 248)'
                                            },
                                            {
                                                'if': {'column_id': 'ticker'},
                                                'textAlign': 'left'
                                            },
                                            {
                                                'if': {'column_id': 'id'},
                                                'display': 'none'
                                            },
                                        ],
                                        row_selectable="single",
                                        style_as_list_view=True)]),

                                html.Button(
                                    "Rewind",
                                    id='rewind',
                                    type="reset",
                                    className="input button-primary")],
                                className='two columns row tiny-header')
                        ],
                        className="twelve columns row"),
                    # row 5
                    html.Div([

                        html.Div([
                            # holdings table
                            html.Div(
                                [
                                    html.Span("Holdings Metrics: "),
                                    tooltip(
                                        "holdings-tooltip",
                                        """
                                        The holdings metrics table contains
                                        the same metrics as the ticker
                                        screener, but the lookback is the
                                        length of each stock's holding
                                        period. The holdings metrics are
                                        as of the date displayed in the
                                        dropdown date select box. Changes to
                                        holdings that occur later than the date
                                        selected are not displayed.
                                        """)
                                ],
                                className="subtitle padded"),
                            dash_table.DataTable(
                                id='holdings',
                                style_header={
                                    'fontWeight': 'bold',
                                    'backgroundColor': 'rgb(230, 230, 230)'},
                                style_cell_conditional=[
                                    {
                                        'if': {'column_id': 'ticker'},
                                        'textAlign': 'left'
                                    },
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(248, 248, 248)'
                                    }],
                                style_as_list_view=True)
                            ],
                            className='six columns row'),

                        html.Div([
                            # portfolio table
                            html.Div(
                                [
                                    html.Span("Portfolio Metrics: "),
                                    tooltip(
                                        "portfolio-tooltip",
                                        """
                                        The portfolio metrics table contains
                                        the same metrics as the holdings
                                        metrics table, but the lookback is the
                                        length of the portfolio holding
                                        period.  The portfolio metrics are
                                        as of the date displayed in the
                                        dropdown date select box. Changes to
                                        the portfolio that occur later than the
                                        date selected are not displayed.
                                        """)
                                ],
                                className="subtitle padded"),
                            dash_table.DataTable(
                                id='portfolio',
                                style_header={
                                    'fontWeight': 'bold',
                                    'backgroundColor': 'rgb(230, 230, 230)'},
                                style_cell_conditional=[
                                    {
                                        'if': {'row_index': 'odd'},
                                        'backgroundColor': 'rgb(248, 248, 248)'
                                    },
                                    {
                                        'if': {'column_id': 'ticker'},
                                        'textAlign': 'left'
                                    }],
                                style_as_list_view=True)
                            ],
                            className='six columns row')
                        ],
                        className='twelve columns row'),
                    # row 6
                    html.Div([
                        # Portfolio Value Chart
                        html.Div([
                            html.Div([
                                html.Span('Portfolio Values: '),
                                tooltip(
                                    "portfolio-values-tooltip",
                                    """
                                    The Portfolio Values chart displays
                                    the value history for each holding.
                                    It displays the value history up
                                    until the date selected in the
                                    dropdown trade date select box. The
                                    S&P 500 is added here as a placeholder
                                    so the colors of holdings are the same
                                    across all charts.
                                    """)
                                ],
                                className="subtitle padded"),
                            dcc.Graph(
                                id='portfolio_performance_linechart')
                            ],
                            className="six columns row"),

                        # Portfolio Gain Chart
                        html.Div([
                            html.Div([
                                html.Span('Portfolio Gain: '),
                                tooltip(
                                    "portfolio-gains-tooltip",
                                    """
                                    The Portfolio Gain chart displays
                                    the return history for each holding.
                                    It displays the return history up
                                    until the date selected in the
                                    dropdown trade date select box.
                                    """),
                                ],
                                className="subtitle padded"),
                            dcc.Graph(
                                id='portfolio_performance_gain_linechart',)
                            ],
                            className="six columns row")
                        ],
                        className="twelve columns row"),
                    # row 7
                    html.Div([
                        # scatter plot
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span(
                                            'Volatility versus Return: '),
                                        tooltip(
                                            "vol_vs_return-tooltip",
                                            """
                                            The Volatility versus Return chart
                                            displays a scatter plot of each
                                            holding's cumulative return versus
                                            its volatility.  It is as of the
                                            date selected in the dropdown trade
                                            date select box. Cash is added here
                                            as a placeholder so the colors of
                                            holdings are the same across all
                                            charts.
                                            """)
                                    ],
                                    className="subtitle padded"),
                                dcc.Graph(
                                    id='vol_vs_return_scatterplot')
                            ],
                            className='six columns row'),
                        # stock return barchart
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.Span('Holdings Returns: '),
                                        tooltip(
                                            "holdings-returns-tooltip",
                                            """
                                            The Holdings Returns bar chart
                                            displays the cumulative return for
                                            each holding in the portfolio.  It
                                            is as of the date selected in the
                                            dropdown trade date select box.
                                            """)
                                    ],
                                    className="subtitle padded"),
                                dcc.Graph(
                                    id='stock_returns_barchart')
                            ],
                            className='six columns row')
                        ],
                        className='twelve columns row')
                    ],
                    id='page-content',
                    className='content')
                ],
                style={'width': '500'},
                className='content-container'),
            dcc.Location(id='url', refresh=False)
        ])


layout = serve_layout
