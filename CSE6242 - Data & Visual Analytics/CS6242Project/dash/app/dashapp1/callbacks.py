import sys
from flask import session
from app import db
import pandas as pd
import datetime
import plotly.graph_objs as go
import dash
import dash_html_components as html
from dash.dependencies import Input
from dash.dependencies import Output


def insert_txn(
        userid,
        date,
        code,
        permno,
        value,
        shares,
        price,
        contra
):
    id = None
    sql = """
        insert into transactions(
            user_id,
            date,
            code,
            permno,
            value,
            shares,
            price,
            contra)
        values(
            %(userid)s,
            %(date)s,
            %(code)s,
            %(permno)s,
            %(value)s,
            %(shares)s,
            %(price)s,
            %(contra)s)
        on conflict(
            user_id,
            date,
            permno,
            code)
        do update set
            value = transactions.value + EXCLUDED.value,
            shares = transactions.shares + EXCLUDED.shares
        returning id
        """
    args = {
        'userid': userid,
        'date': date,
        'code': code,
        'permno': permno,
        'value': value,
        'shares': shares,
        'price': price,
        'contra': contra}
    conn = db.engine.connect()
    trans = conn.begin()
    try:
        res = conn.execute(sql, args)
        for row in res:
            id = row['id']
        trans.commit()
    except Exception as e:
        # print('txn fail - rolling back: %s' % args, file=sys.stderr)
        # print('error: %s' % e)
        trans.rollback()
    return id


def check_cash(userid, date):
    sql = """
        select value
        from holdings
        where permno = 0
            and user_id = %(userid)s
            and date = getmarketdate(%(date)s)
        """
    args = {'userid': userid, 'date': date}
    df = pd.read_sql(sql, con=db.engine, params=args)
    if len(df) == 0:
        cash = 0
    else:
        cash = df['value'].iloc[0]
    return cash


def get_current_value(userid, date, permno):
    sql = """
        select h.value
        from holdings h
        where h.permno = %(permno)s
            and h.user_id = %(userid)s
            and h.date = getmarketdate(%(date)s)
    """
    args = {'date': date, 'permno': permno, 'userid': userid}
    # print('currvalue args: %s' % args, file=sys.stderr)
    df = pd.read_sql(sql, con=db.engine, params=args)
    # print('currvalue df: %s' % df, file=sys.stderr)
    value = df['value'].iloc[0]
    return value


def register_callbacks(dashapp):
    # missing buy/sell alert
    @dashapp.callback(
        [
            Output('side_alert', 'is_open'),
            Output('side_alert', 'children')],
        [Input('side', 'value')]
    )
    def alert_side(value):
        show_alert = False
        msg = ""
        if value is None or value == '':
            show_alert = True
            msg = "No Buy/Sell chosen.  Please choose a side."
        return (show_alert, msg)

    # 0 value alert
    @dashapp.callback(
        [
            Output('value_alert', 'is_open'),
            Output('value_alert', 'children')],
        [Input('value', 'value')]
    )
    def alert_value(value):
        show_alert = False
        msg = ""
        if value is None or value == 0:
            show_alert = True
            msg = "Value is 0. Please choose a value."
        return (show_alert, msg)

    # current username
    @dashapp.callback(
        Output('username', 'children'),
        [Input('page-content', 'children')])
    def cur_user(input1):
        name = session.get('username', None)
        return name.capitalize()

    # current userid
    @dashapp.callback(
        Output('userid', 'children'),
        [Input('page-content', 'children')])
    def cur_user_id(input1):
        userid = session.get('userid', None)
        # print("userid: %s" % userid, file=sys.stderr)
        return userid

    # logout button
    @dashapp.callback(
        Output('logout', 'children'),
        [Input('page-content', 'children')])
    def user_logout(input1):
        return html.A('logout', href='/logout')

    # date picker
    @dashapp.callback(
        [
            Output('datepicker', component_property='min_date_allowed'),
            Output('datepicker', component_property='max_date_allowed'),
            Output('datepicker', component_property='initial_visible_month'),
            Output('datepicker', component_property='date')],
        [
            Input('submit', 'n_clicks'),
            Input('rewind', 'n_clicks'),
            Input('dateslider', 'value')])
    def datepicker(submit_clicks, rewind_clicks, slider_value):
        # 2019 = 13 - which is out of our range
        end_month = None
        end_day = None
        if slider_value is None or slider_value == 0:
            slider_value = 1
        if slider_value > 12:
            slider_value = 12
            end_month = 12
            end_day = 31

        year_dict = {
            1: 2007,
            2: 2008,
            3: 2009,
            4: 2010,
            5: 2011,
            6: 2012,
            7: 2013,
            8: 2014,
            9: 2015,
            10: 2016,
            11: 2017,
            12: 2018,
        }
        slide_year = year_dict[slider_value]

        # print('slider value: %s' % slider_value, file=sys.stderr)
        userid = session.get('userid', None)
        sql = """
            select greatest(max(date), '2007-01-03') as start_date,
            '2018-12-31' as end_date
            from transactions
            where user_id = %s
                and not auto
            """

        df = pd.read_sql(sql, con=db.engine, params=[userid])
        row = df.iloc[0]
        sd = row['start_date']
        year = max(sd.year, slide_year)
        # these values deal with the case where the slider
        # is on 2019, so we want the date to be 2018-12-31
        if end_month is None:
            month = sd.month
        else:
            month = end_month
        if end_day is None:
            day = sd.day
        else:
            day = end_day
        start_date = datetime.date(year, month, day)
        end_date = row['end_date']
        return (
            start_date,
            end_date,
            start_date,
            str(start_date))

    # side dropdown box is not dynamic so is not in callbacks
    # this note is a placeholder to where it exists in the form

    # ticker dropdown box
    @dashapp.callback(
        Output('ticker', component_property='options'),
        [
            Input('datepicker', 'date'),
            Input('side', 'value'),
            Input('rewind', 'n_clicks')
        ])
    def get_dropdown_ticker_list(date, code, rewind_clicks):
        userid = session.get('userid', None)

        # print("code: %s" % code, file=sys.stderr)

        # print("date: %s" % date, file=sys.stderr)
        if code == 'B':
            sql = """
                select
                    ticker || ' - ' || comnam as label,
                    permno::int as value
                from stockmaster
                where ticker is not null
                and case when %(date)s is not null then
                        %(date)s::timestamp <@ tsrange(st_date, end_date, '[]')
                    else
                        1 = 1
                    end
                group by ticker, comnam, permno
                order by permno = 0 desc, ticker, permno
                """
            args = {'date': date}
        else:
            sql = """
                select s.ticker || ' - ' || comnam as label,
                    s.permno::int as value
                from stockmaster s
                inner join holdings h
                    on h.permno = s.permno
                where ticker is not null
                    and h.value > 0
                    and h.user_id = %(userid)s
                    and h.date = getmarketdate(%(date)s)
                    and %(date)s::timestamp <@ tsrange(st_date, end_date, '[]')
                group by s.ticker, s.comnam, s.permno
                order by s.permno = 0 desc, s.ticker, s.permno
            """
            args = {'date': date, 'userid': userid}
        df = pd.read_sql(sql, con=db.engine, params=args)
        dropdown = df.to_dict('records')
        return dropdown

    # dollar value input box
    @dashapp.callback(
        Output('value', 'max'),
        [
            Input('datepicker', 'date'),
            Input('ticker', 'value'),
            Input('side', 'value'),
            Input('submit', 'n_clicks')])
    def populate_value(date, permno, side, submit_clicks):
        userid = session.get('userid', None)
        # when not the default values below the submit callback
        # this fires again resetting the default causing a double insert
        # update submits here too prevent this from hap[ening]
        if submit_clicks is None:
            submit_clicks = 0
            session['submit_clicks'] = 0
        else:
            session['submit_clicks'] = submit_clicks
        if permno is not None and permno != 0:
            if side == 'B':
                max_value = 99999999.99
            elif side == 'S':
                value = get_current_value(userid, date, permno)
                max_value = value
        else:
            if side == 'B':
                max_value = 99999999.99
            elif side == 'S':
                max_value = 0
        return max_value

    # submit button
    # this button controls transactions so the logic
    # for it is in the transactions callback

    # transactions radio box
    # controlled by both the submit and rewind buttons
    @dashapp.callback(
        [
            Output('transactions', component_property='columns'),
            Output('transactions', component_property='data'),
            Output('ticker_alert', 'is_open'),
            Output('ticker_alert', 'children')
        ],
        [
            Input('datepicker', 'date'),
            Input('ticker', 'value'),
            Input('side', 'value'),
            Input('value', 'value'),
            Input('submit', 'n_clicks'),
            Input('rewind', 'n_clicks')
        ])
    def submit_transaction(date, permno, code, value, clicks, rewind):
        show_alert = False
        msg = ""
        idx = None
        userid = session.get('userid', None)
        loading = session.get('loading', None)
        # permno from ticker dropdown is a string, so convert to an int
        if permno is not None:
            permno = int(permno)
        else:
            show_alert = True
            msg = "Ticker is empty. Please select a ticker."
            return (dash.no_update, show_alert, msg)

        # print(
        #     'submit init values: %s' % (
        #         [userid, date, code, permno, value]), file=sys.stderr)
        # print('clicks param: %s' % clicks, file=sys.stderr)
        if clicks is None:
            clicks = 0
            prev_clicks = clicks
            session['submit_clicks'] = clicks
        else:
            prev_clicks = session['submit_clicks']

        # print(
        #     'submit clicks: %s, prev_clicks: %s' % (
        #         clicks, prev_clicks), file=sys.stderr)
        if clicks > prev_clicks:
            # if loading is not None:
            #    show_alert = True
            #    msg = "Still Processing...  Please try again."
            #     return (dash.no_update, show_alert, msg)
            session['loading'] = 1
            sql = """
                select
                    dsf.prc / dsf.cfacpr as price,
                    %(value)s / ( dsf.prc / dsf.cfacpr) as shares
                from  dsf
                where permno = %(permno)s
                    and date = getmarketdate(%(date)s)
                """
            args = {'value': value, 'permno': permno, 'date': date}
            df = pd.read_sql(sql, con=db.engine, params=args)
            shares = df['shares'].iloc[0]
            price = df['price'].iloc[0]

            if permno is not None:
                if code == 'B':
                    if permno != 0:
                        # buying stock
                        cash = check_cash(userid, date)
                        # print('cash: %s' % cash)
                        if cash >= value:
                            idx = insert_txn(
                                userid,
                                date,
                                'S',
                                0,
                                value,
                                value,
                                1,
                                idx)
                            insert_txn(
                                userid,
                                date,
                                code,
                                permno,
                                value,
                                shares,
                                price,
                                idx)
                            # print("txn 1: %s %s %s %s %s %s %s %s" % (
                            #     userid,
                            #     date,
                            #     code,
                            #     permno,
                            #     value,
                            #     shares,
                            #     price,
                            #     idx))
                    else:
                        # depositing cash
                        if value is not None:
                            insert_txn(
                                userid,
                                date,
                                code,
                                permno,
                                value,
                                shares,
                                price,
                                idx)
                            # print("txn 2: %s %s %s %s %s %s %s %s" % (
                            #      userid,
                            #     date,
                            #     code,
                            #     permno,
                            #     value,
                            #     shares,
                            #     price,
                            #     idx))
                elif code == 'S':
                    if permno != 0:
                        curr_value = get_current_value(userid, date, permno)
                        if value > curr_value:
                            value = curr_value
                        if value is not None:
                            idx = insert_txn(
                                userid,
                                date,
                                code,
                                permno,
                                value,
                                shares,
                                price,
                                None)
                            insert_txn(
                                userid,
                                date,
                                'B',
                                0,
                                value,
                                value,
                                1,
                                idx)
                            # print("txn 3: %s %s %s %s %s %s %s %s" % (
                            #     userid,
                            #     date,
                            #     code,
                            #     permno,
                            #     value,
                            #     shares,
                            #     price,
                            #     idx))

        sql = """
            select id, TO_CHAR(t.date, 'YYYY-MM-DD') as date,
                case when t.code = 'B' then
                        'BUY'
                    else
                        'SELL'
                    end as side,
                    s.ticker as ticker,
                    to_char(t.value, 'FM$999,999,999,990D00') as value
            from transactions t
            inner join stockmaster s
                on t.permno = s.permno
                    and t.date::timestamp
                        <@ tsrange(st_date, end_date, '[]')
            where t.user_id = %s
            order by t.id asc
            """
        df = pd.read_sql(sql, con=db.engine, params=[userid])
        columns = [{"name": i.capitalize(), "id": i} for i in df.columns]
        data = df.to_dict('records')

        return (columns, data, show_alert, msg)

    # ticker screener
    # populates the ticker summare metrics from the ticker selected
    # in the ticker dropdown using the date from the datepicker
    @dashapp.callback(
        [
            Output('screener', component_property='columns'),
            Output('screener', component_property='data')],
        [
            Input('ticker', 'value'),
            Input('datepicker', 'date')])
    def populate_ticker_screener_table(permno, date):
        sql = """
            select ticker,
                m.date,                                
                dsf.prc / dsf.cfacpr as price,
                alpha * 100 as "alpha (%%)",
                beta,
                coalesce(sharpe, 0) as sharpe,
                coalesce(sortino, 0) as sortino,
                volatility * 100 as "volatility (%%)"
            from metrics m
            inner join dsf on dsf.permno = m.permno
                and dsf.date = m.date
            inner join stockmaster s
                on m.permno = s.permno
                    and m.date::timestamp
                        <@ tsrange(st_date, end_date, '[]')
            where m.permno = %(permno)s
                and m.date = getmarketdate(%(date)s)
            """
        args = {'permno': permno, 'date': date}
        df = pd.read_sql(sql, con=db.engine, params=args)
        df = df.round(4)
        df = df.transpose()
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'Metric', 0: 'Value'}, inplace=True)
        df['Metric'] = df['Metric'].str.capitalize()
        columns = [{"name": i.capitalize(), "id": i} for i in df.columns]
        data = df.to_dict('records')
        return (columns, data)

    # holdings table
    # this gets populated from the transactions table
    # after the updateholdings function is fired
    # rewund button logic is also in here to rewind transactions
    @dashapp.callback(
        [
            Output('holdings', component_property='columns'),
            Output('holdings', component_property='data'),
            Output('rewind_alert', 'is_open'),
            Output('rewind_alert', 'children')],
        [
            Input('transactions', 'selected_rows'),
            Input('transactions', 'data'),
            Input('datepicker', 'date'),
            Input('rewind', 'n_clicks'),
            Input('submit', 'n_clicks')])
    def rewind_transactions(
            selected,
            data,
            date,
            rewind_clicks,
            submit_clicks
    ):
        show_alert = False
        msg = ""
        userid = session.get('userid', None)
        loading = session.get('loading', None)

        # print('date: %s' % date)
        # print('selected: %s' % selected, file=sys.stderr)
        # print('data: %s' % data, file=sys.stderr)
        if len(selected) > 0:
            row = selected[0]
            if len(data) >= row + 1:
                idx = data[selected[0]]['id']
            else:
                idx = None
        else:
            idx = None
        # print('idx: %s, date: %s' % (idx, date))
        if rewind_clicks is None:
            rewind_clicks = 0
            prev_rewind_clicks = rewind_clicks
            session['rewind_clicks'] = rewind_clicks
        else:
            prev_rewind_clicks = session['rewind_clicks']
        if submit_clicks is None:
            submit_clicks = 0
            prev_submit_clicks = submit_clicks
            session['submit_clicks'] = submit_clicks
        else:
            prev_submit_clicks = session['submit_clicks']
        args = {'userid': userid, 'idx': idx}
        # print("Rewind clicks - curr: %s: prev: %s" % (
        #     rewind_clicks, prev_rewind_clicks), file=sys.stderr)
        # print("Submit clicks - curr: %s: prev: %s" % (
        #     submit_clicks, prev_submit_clicks), file=sys.stderr)
        conn = db.engine.connect()
        if (
                rewind_clicks > prev_rewind_clicks
                or submit_clicks > prev_submit_clicks
        ):
            # if loading is not None:
            #    show_alert = True
            #    msg = "Still Processing...  Please try again."
            #    return (dash.no_update, dash.no_update, show_alert, msg)
            session['loading'] = 1
            if submit_clicks > prev_submit_clicks:
                session['submit_clicks'] = submit_clicks
            if rewind_clicks > prev_rewind_clicks:
                sql = "select delete_txns(%(userid)s, %(idx)s)"
                trans = conn.begin()
                try:
                    conn.execute(sql, args)
                    trans.commit()
                    # print('Deleted txns for user: %s, id>= %s' % (
                    #     userid, idx), file=sys.stderr)
                except Exception:
                    trans.rollback()
        trans = conn.begin()
        try:
            conn.execute(
                "select autoclose_positions(%(userid)s)", args)
            conn.execute(
                "select updateholdings(%(userid)s)", args)
            conn.execute(
                "select refreshportfolio(%(userid)s)", args)
            trans.commit()
        except Exception as e:
            trans.rollback()
            # print('Rewind - upd hold & port error: %s' % e, file=sys.stderr)
        finally:
            session.pop('loading', None)
            conn.close()

        sql = """
            select s.ticker,
                h.date,
                to_char(h.value, 'FM$999,999,999,990D00') as value,
                round((
                    h.value
                    / sum(h.value)
                    over (partition by user_id)
                        )::numeric * 100, 2) as port_pct,
                cumret * 100 as cumret,
                cumret_sp500 * 100 as cumret_sp500,
                alpha * 100 as alpha,
                beta,
                sharpe,
                sortino,
                volatility * 100 as volatility
            from holdingsgain h
            inner join stockmaster s
                on s.permno = h.permno
            where h.user_id = %(userid)s
                and h.date = getmarketdate(%(date)s)
                and case when h.permno <> 0 then h.value > 0 else 1=1 end
                and %(date)s::timestamp <@ tsrange(st_date, end_date, '[]')
            order by h.permno = 0 desc,
                ticker asc
            """
        args = {'userid': userid, 'date': date}
        df = pd.read_sql(sql, con=db.engine, params=args)
        df = df.round(2)
        session['rewind_clicks'] = rewind_clicks
        # print('Holdings: %s' % df.to_dict('records'), file=sys.stderr)
        rename = {
            'port_pct': 'portfolio (%)',
            'cumret': 'tot ret (%)',
            'cumret_sp500': 'sp500 tot (%)',
            'alpha': 'alpha (%)',
            'volatility': 'volatility (%)'
        }
        df.rename(columns=rename, inplace=True)
        columns = [{"name": i.capitalize(), "id": i} for i in df.columns]
        data = df.to_dict('records')
        return (columns, data, show_alert, msg)

    # portfolio table
    # this table is also updated from the transactions table
    # after the updateholdings and refreshportfolio functions
    # are called
    @dashapp.callback(
        [
            Output('portfolio', component_property='columns'),
            Output('portfolio', component_property='data')],
        [
            Input('holdings', 'data'),
            Input('datepicker', 'date'),
            Input('rewind', 'n_clicks'),
            Input('submit', 'n_clicks')])
    def display_portfolio_metrics(
            holdings, date, rewind_clicks, submit_clicks
    ):
        userid = session.get('userid', None)
        # print(
        #     'Portfolio Table Update - userid: %s, date: %s' % (
        #         userid, date), file=sys.stderr)
        sql = """
            select  date,
                to_char(value, 'FM$999,999,999,990D00') as value,
                cumret * 100 as cumret,
                cumret_sp500 * 100 as cumret_sp500,
                alpha * 100 as alpha,
                beta,
                sharpe,
                sortino,
                volatility * 100 as volatility
            from portfoliogain
            where user_id = %(userid)s
                and date = getmarketdate(%(date)s)
            """
        args = {'userid': userid, 'date': date}
        df = pd.read_sql(sql, con=db.engine, params=args)
        df = df.round(2)
        rename = {
            'cumret': 'tot ret (%)',
            'cumret_sp500': 'sp500 tot (%)',
            'alpha': 'alpha (%)',
            'volatility': 'volatility (%)'}
        df.rename(columns=rename, inplace=True)
        columns = [{"name": i.capitalize(), "id": i} for i in df.columns]
        data = df.to_dict('records')
        return (columns, data)

    # stock chart
    # this chart is controlled by the ticker dropdown box
    # with the max date coming form the date picker
    @dashapp.callback(
        Output('stock', 'figure'),
        [
            Input('ticker', 'value'),
            Input('datepicker', 'date'),
            Input('screener', 'selected_row_ids'), ])
    def update_graph(permno, date, screener_ids):
        sql = """
            select m.date,
                dsf.prc / dsf.cfacpr as price,
                beta,
                volatility
            from metrics m
            inner join dsf on dsf.permno = m.permno
                and dsf.date = m.date
            where m.permno = %(permno)s
                and m.date <= getmarketdate(%(date)s)
            order by m.date
            """
        args = {'permno': permno, 'date': date}
        df = pd.read_sql(sql, params=args, con=db.engine)
        chart_data = []
        for col in df.columns[1:]:
            # add a line to the line chart for the portfolio
            # and each indiv stock
            if col == 'price':
                vis = True
            else:
                vis = 'legendonly'
            chart_data.append(
                go.Scatter(x=df['date'], y=df[col], name=col, visible=vis))
        return {
            'data': chart_data,
            'layout': go.Layout(
                title='Dropdown Ticker History',
                yaxis={'title': 'Price'},
                yaxis_type="log",
                yaxis_tickformat=".2f",
                height=400)
        }

    # portfolio and holdings values line chart
    # this chart refreshes when the holdings table changes
    # or the date changes in the date picker
    @dashapp.callback(
        Output('portfolio_performance_linechart', 'figure'),
        [
            Input('holdings', 'data'),
            Input('datepicker', 'date')])
    def update_performance_linechart(holdings, date):
        # print("Performance Values got callback")
        userid = session.get('userid', None)
        sql = """
            select p.date, 
                p.value as portfolio, 
                0 as sp500, 
                s.ticker, 
                h.value
            from portfolio p
            inner join holdings h
                on h.user_id = p.user_id
                    and p.date = h.date
            inner join stockmaster s
                on h.permno = s.permno
                    and h.date::timestamp
                        <@ tsrange(s.st_date, s.end_date, '[]')
            where p.user_id = %(userid)s
                and h.value > 0
                and h.date <= getmarketdate(%(date)s)
            order by date, ticker
            """
        args = {'userid': userid, 'date': date}
        df = pd.read_sql(sql, con=db.engine, params=args)
        # print('values df: %s' % df)
        stocks = df[
            ['date', 'ticker', 'value']
        ].pivot(index='date', columns='ticker', values='value')
        df.drop(columns=['ticker', 'value'], inplace=True)
        df = df.merge(stocks, on='date', how='inner')
        df.columns = map(str.upper, df.columns)

        port_value_chart_line_data = []
        # For loop to add components to line and scatter plot:
        # mostly used just for the iterative name=col at the end
        # (rest could be done using lists)
        for col in df.columns[1:]:
            # add a line to the line chart for the portfolio
            # and each indiv stock
            if col != 'SP500':
                vis = True
            else:
                vis = 'legendonly'
            port_value_chart_line_data.append(
                go.Scatter(x=df['DATE'], y=df[col], name=col, visible=vis))

        return {
            'data': port_value_chart_line_data,
            'layout': go.Layout(
                title='Portfolio Values',
                yaxis={'title': '$ Value'})}

    # portfolio and holdings returns line chart
    # this chart refreshes when the holdings table changes
    # or the date changes in the date picker
    @dashapp.callback(
        Output('portfolio_performance_gain_linechart', 'figure'),
        [
            Input('holdings', 'data'),
            Input('datepicker', 'date')])
    def update_performance_gain_linechart(holdings, date):
        userid = session.get('userid', None)
        sql = """
            select p.date,
                round((p.cumret * 100)::numeric, 2) as portfolio,
                round((p.cumret_sp500 * 100)::numeric, 2) as sp500,
                s.ticker,
                round((h.cumret * 100)::numeric, 2) as ret
            from portfoliogain p
            inner join holdings h
                on h.user_id = p.user_id
                    and p.date = h.date
            inner join stockmaster s
                on h.permno = s.permno
                    and h.date::timestamp
                        <@ tsrange(s.st_date, s.end_date, '[]')
            where p.user_id = %(userid)s
                and h.value > 0
                and h.date <= getmarketdate(%(date)s)
            order by date, ticker
            """
        args = {'userid': userid, 'date': date}
        df = pd.read_sql(sql, con=db.engine, params=args)
        stocks = df[
            ['date', 'ticker', 'ret']
        ].pivot(index='date', columns='ticker', values='ret')
        df.drop(columns=['ticker', 'ret'], inplace=True)
        df = df.merge(stocks, on='date', how='inner')
        df.columns = map(str.upper, df.columns)

        port_value_chart_line_data = []
        # For loop to add components to line and scatter plot:
        # mostly used just for the iterative name=col at the end
        # (rest could be done using lists)
        for col in df.columns[1:]:
            # add a line to the line chart for the portfolio and
            # each indiv stock
            port_value_chart_line_data.append(
                go.Scatter(x=df['DATE'], y=df[col], name=col))

        return {
            'data': port_value_chart_line_data,
            'layout': go.Layout(
                title='Portfolio Gain',
                yaxis={'title': '% Gain'})}

    # return versus volatility scatter plot
    # this chart refreshes when the holdings table changes
    # or the date changes in the date picker
    @dashapp.callback(
        Output('vol_vs_return_scatterplot', 'figure'),
        [
            Input('holdings', 'data'),
            Input('datepicker', 'date')])
    def get_scatterplot(holdings, date):
        userid = session.get('userid', None)

        sql = """
            select 'PORTFOLIO' as ticker, 
                cumret * 100 as cumret,
                volatility * 100 as volatility, 
                1 as idx
            from portfoliogain p
            where user_id = %(userid)s
                and date = getmarketdate(%(date)s)

            union

            select 'SP500',
                cumret_sp500 * 100,
                volatility_sp500 * 100,
                2 as idx
            from portfoliogain
            where user_id = %(userid)s
                and date = getmarketdate(%(date)s)

            union

            select tickerfrompermno(h.permno, h.date),
                h.cumret * 100,
                h.volatility * 100,
                (row_number()
                    over
                        (order by tickerfrompermno(h.permno, h.date))) + 2 as idx
            from holdings h
            inner join (
                select user_id, permno, max(date) as date
                from holdings
                where user_id = %(userid)s
                    and date <= %(date)s
                group by user_id, permno
            ) mh on mh.permno = h.permno
                and mh.date = h.date
                and mh.user_id = h.user_id
            order by idx
            """
        args = {'userid': userid, 'date': date}
        df = pd.read_sql(sql, con=db.engine, params=args)

        # For loop to add components to line and scatter plot:
        # mostly used just for the iterative name=col at the end
        # (rest could be done using lists)
        data = []
        for row in df.itertuples():
            ticker = row.ticker
            cumret = row.cumret
            vol = row.volatility
            # add a dot to the scatterplot
            if ticker != 'CASH':
                vis = True
            else:
                vis = 'legendonly'
            data.append(
                go.Scatter(
                    x=[cumret],
                    y=[vol],
                    mode='markers',
                    name=ticker,
                    visible=vis))

        return {
            'data': data,
            'layout': go.Layout(
                title='Volatility vs. Return',
                xaxis={'title': 'Return'},
                yaxis={'title': 'Volatility'})}

    # portfolio and holdings bar chart
    # this chart refreshes when the holdings table changes
    # or the date changes in the date picker
    @dashapp.callback(
        Output('stock_returns_barchart', 'figure'),
        [
            Input('holdings', 'data'),
            Input('datepicker', 'date')])
    def get_indiv_port_returns(holdings, date):
        userid = session.get('userid', None)
        sql = """
            select 'PORTFOLIO' as ticker, cumret * 100 as cumret, 1 as idx
            from portfoliogain p
            where user_id = %(userid)s
                and date = getmarketdate(%(date)s)

            union

            select 'SP500', cumret_sp500 * 100, 2 as idx
            from portfoliogain
            where user_id = %(userid)s
                and date = getmarketdate(%(date)s)

            union

            select tickerfrompermno(h.permno, h.date),
                h.cumret * 100,
                (row_number()
                    over
                        (order by h.cumret)) + 2 as idx
            from holdings h
            inner join (
                select user_id, permno, max(date) as date
                from holdings
                where permno <> 0
                    and user_id = %(userid)s
                    and date <= %(date)s
                group by user_id, permno
            ) mh on mh.permno = h.permno
                and mh.date = h.date
                and h.user_id = mh.user_id
            order by idx
            """
        args = {'userid': userid, 'date': date}
        df = pd.read_sql(sql, con=db.engine, params=args)

        indiv_port_returns = go.Bar(
            x=df['ticker'].tolist(),
            y=df['cumret'].tolist(), name='indiv_returns')

        return {
            'data': [indiv_port_returns],
            'layout': go.Layout(
                title='Holdings Returns',
                yaxis={'title': '% Total Return'})}
