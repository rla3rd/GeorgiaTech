import os
import sys
import traceback
import glob
import pandas as pd
from sqlalchemy import create_engine
import psycopg2
import io
import argparse

if __name__ == '__main__:'

    parser = argparse.ArgumentParser()
    parser.add_argument('-h', '--host', type=str, dest='host', help='database host', default='localhost')
    parser.add_argument('-p', '--port', type=str, dest='port', help='database port', default=5432)
    parser.add_argument('-u', '--user', type=str, dest='user', help='database username', default='crsp')
    parser.add_argument('-P', '--password', type=str, dest='password', help='database password', default=None)
    options = parser.parse_args()

    if options.password is None:
        print ('must supply a passwod')

    engine = create_engine('postgresql+psycopg2://%s:%s@%s:%s/crsp' % (
        options.user, options.password, options.host, options.port)
    conn = engine.raw_connection()
    cursor = conn.cursor()



    file_list = glob.glob('parquet/*parquet')
    print(file_list)

    for file_name in file_list:
        (path, sfx) = file_name.split('.')
        (basdir, base) = path.split("/")
        print('base: %s' % base)

        df = pd.read_parquet(file_name, engine='pyarrow')

        try:
            # dsf is handled with its own script since pandas chokes on loading it
            if base !='dsf':
                print('%s loading...' % base)
                output = io.StringIO()
                df.to_csv(output, sep='\t', header=False, index=False)
                output.seek(0)
                contents = output.getvalue()
                cursor.copy_from(output, base, null="", columns=df.columns)
                conn.commit()
                print('Finished.')
            except Exception as e:
                print(e)