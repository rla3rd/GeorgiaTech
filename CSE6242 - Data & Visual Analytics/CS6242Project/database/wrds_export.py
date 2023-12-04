import os
import sys
import wrds
import argparse

#db = wrds.Connection(wrds_username='rla3rd', wrds_password='JMUbeTiFwwm4J5KZ')

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('-u', '--user', type=str, dest='user', help='wrds username', default=None)
    parser.add_argument('-p', '--password', type=str, dest='password', help='wrds password', default=None)
    
    options = parser.parse_args()
    
    if options.user is None or options.password is None:
        print('must supply a username and password')
        sys.exit(1)
    
    db = wrds.Connection(wrds_username=options.user, wrds_password=options.password)
    libraries = db.list_libraries()
    tables = db.list_tables('crsp_a_stock')

    table_desc = {}
    file_list = []
    for table in tables:
        try:
            file_name = 'parquet/%s.parquet' % table
            if not os.path.exists(file_name) and table != 'dsf':
                print('%s loading...' % table)
                df = db.get_table('crsp_a_stock', table)
                df.to_parquet(file_name, engine='pyarrow')
                print('Finished.')
            file_list.append(file_name)
        except Exception as e:
            print(e)
    sys.exit(0)
