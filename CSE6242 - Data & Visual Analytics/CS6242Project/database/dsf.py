import pandas as pd
import subprocess
import glob
import shutil
import os
import io
import argparse
from sqlalchemy import create_engine

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-h', '--host', type=str, dest='host', help='database host', default='localhost')
    parser.add_argument('-p', '--port', type=str, dest='port', help='database port', default=5432)
    parser.add_argument('-u', '--user', type=str, dest='user', help='database username', default='crsp')
    parser.add_argument('-P', '--password', type=str, dest='password', help='database password', default=None)
    options = parser.parse_args()

    engine = create_engine('postgresql+psycopg2://%s:%s@%s:%s/crsp' % (
        options.user, options.password, options.host, options.port)
    conn = engine.raw_connection()
    cursor = conn.cursor()

    cwd = os.getcwd()

    df = pd.read_sas('parquet/dsf/dsf.sas7bdat')
    df.to_csv('parquet/dsf/dsf.csv', index=False)
    subprocess.check_output("splitcsv parquet/dsf/dsf.csv"
    filenames = glob.glob('output/*csv')
    for filenm in filenames:
        try:
            df = pd.read_csv(filenm)
            output = io.StringIO()
            df.to_csv(output, sep='\t', header=False, index=False)
            output.seek(0)
            contents = output.getvalue()
            cursor.copy_from(output, "dsf", null="", columns=df.columns)
            conn.commit()
        except Exception as e:
            print(e) 
    shutil.rmtree('output')
