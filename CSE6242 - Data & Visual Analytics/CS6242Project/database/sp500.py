# the csv uploaded by this script came from
# downloading the compustat constituents from the wrds website
# https://wrds-web.wharton.upenn.edu/wrds/ds/compd/index/constituents.cfm?navId=83
# select Index Constituents
# select GVKEYX 000003
# select all variables
# select csv
# right click file on Data Request Summary Page
# save as 
# sp500.csv


import os
import datetime
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import psycopg2
import io
import argparse

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-h', '--host', type=str, dest='host', help='database host', default='localhost')
    parser.add_argument('-p', '--port', type=str, dest='port', help='database port', default=5432)
    parser.add_argument('-u', '--user', type=str, dest='user', help='database username', default='crsp')
    parser.add_argument('-P', '--password', type=str, dest='password', help='database password', default=None)
    options = parser.parse_args()

    engine = create_engine('postgresql+psycopg2://%s:%s@%s:%s/crsp' % (
        options.user, options.password, options.host, options.port)
    df = pd.read_csv('parquet/sp500.csv', parse_dates=['from', 'thru'])

    df.head(0).to_sql('sp500', engine, if_exists='replace', index=False)
    conn = engine.raw_connection()
    cur = conn.cursor()
    output = io.StringIO()
    df.to_csv(output, sep='\t', header=False, index=False)
    output.seek(0)
    contents = output.getvalue()
    cur.copy_from(output, 'sp500', null="")
    conn.commit()
