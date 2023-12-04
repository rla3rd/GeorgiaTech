# CSE6242 Portfolio Analysis Tool
Our project architecture is based upon the following works:

## Dash on flask with flask_login
An example of a seamless integration of a Dash app into an existing Flask app based on the application factory pattern.

For details and how to use, please read: https://medium.com/@olegkomarov_77860/how-to-embed-a-dash-app-into-an-existing-flask-app-ea05d7a2210b


## The Flask Mega-Tutorial
An In depth tutorial on getting started with flask.
https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world

# Portfolio Analysis Tool
Our portfolio analysis tool uses the Center for Research in Security Prices yearly dataset. It is available for free as a student of Georgia Tech through the University of Pennsylvania's Wharton Research Data Services portal.  The information is available vie the website, ssh, and via a postgresql interface.  All three methods were used to obtain the data for our project.  The Standard and Poor's 500 index constituents was obtained through the website through the Compustat dataset.  The constituent data was available from 2007 through 2018. All but one of the CRSP data tables was fetched via the postgresql interface.  The CRSP dsf table was too big to fit into pandas memory and upload into our local database at the same time, as pandas makes a copy of the data in order to load it into the database using the dataframe.to_sql method. The table was fetched using the scp command and fetched as a SAS 7 binary file.  The file was then converted to CSV and loaded into our local postgresql database.

# Tool Usage
The tool requires cash to be deposited into the portfolio, similar to an investor's brokerage account.  The stock ticker history ranges from 2014 through 2018.  The portolio start date is 2007, allowing 3 years of prior stock price data to be used for the calculation of beta.  All the other ratios in the ticker screener table of our tool use a one year lookback, so the ratios that start on 1/3/2007 use the daily returns of 2006 as a basis of their calculations.  This table was then precalculated from 2007 through 2018.  

The input entry area of the tool is fully dynamic. the slider at the top of the tool provides an easy way to control the years of the date picker without type a year into the date picker. The minimmum date of the date picker is set by the greater of 1/3/2007 or the date of the last portfolio transaction, ensuring you can only move foreward in time while entering transactions.  Rewind functionality is included in the tool in order to reset a portfolio to a specific point in time in the entering of transactions. If a user decides to sell a transaction, only sales of long positions are allowed, excluding cash.  Cash is exlcuded in order to provide the tool with a way to keep track of realized gains.

The holdings and portfolio table ratios are fully dynanmic as well, and represent the state of the portfolio at a given point in time as specified by the date picker.  The ratios are calculated over the life of the portfolio's holding period.

All charts are also fully dynamic and represent the state of the portfolio at a given point in time as specified by the date picker control.

# Source Code
the source code is located at 
https://github.gatech.edu/rouldnoughi3/CS6242Project

# Demo Site
the application is hosted on Amazon's AWS Elastic Beanstalk service at
http://flaskdash-env.ktnz3wkrdv.us-east-1.elasticbeanstalk.com

the database is hosted on Amazon's RDS service at 
database-1.cudz1l7w5ie2.us-east-1.rds.amazonaws.com

# Installation Steps to run the tool locally using the tool's data
to install the application locally the following steps would need to be taken:

this tutorial assumes an install on a unix like system

Installing with prefiltered data
1. install the python dependencies using the anaconda distribution
	conda install pandas
	conda install flask
	conda install flask-login           
	conda install flask-sqlalchemy     
	conda install flask-wtf           
	conda install dash
	conda install  dash-bootstrap-components
	pip install wrds
2. Install postgresql 11 - follow the documentation for initial database setup
	https://www.postgresql.org/download/
	
3. Create the database as the postgres user
	>create database crsp;
	>create user crsp with encrypted password 'mycustompasword';
	>grant all privileges on database crsp to crsp;
	
4. download the database zip file from here
	https://www.dropbox.com/s/1yhr87a57eonvi8/crsp_schema_data.zip?dl=0
	
	unzip crsp_schema_data.zip

	then install the database schema

	psql -h myhost -p myport -U crsp crsp -f crsp_schema_data.sql

5. modify dash/config.py to point to your database installation

6. run from the project dash dir
	flask run
	open a browser pointed at https://localhost:5000

# Installation steps to run the tool from scratch using data from WRDS
this tutorial assumes an install on a unix like system

1. install the python dependencies using the anaconda distribution
	conda install pandas
	conda install flask
	conda install flask-login           
	conda install flask-sqlalchemy     
	conda install flask-wtf           
	conda install dash
	conda install  dash-bootstrap-components
	pip install wrds

2. Request an account from Wharton Research Data Services
	https://wrds-www.wharton.upenn.edu/
	This can take a few days for approval.
	
3. Install postgresql 11 - follow the documentation for initial database setup
	https://www.postgresql.org/download/
	
4. Create the database as the postgres user
	>create database crsp;
	>create user crsp with encrypted password 'mycustompasword';
	>grant all privileges on database crsp to crsp;
	
5. from the project database/schema directory, install the database schema
	psql -h myhost -p myport -U crsp crsp -f crsp_schema.sql

6. download the source code from 
	https://github.gatech.edu/rouldnoughi3/CS6242Project
	
	
7. Download the data from wrds (from project root dir)
	cd database
	mkdir parquet
	python wrds_export.py -u myuser -p mypassword
	
8. dsf is too big for pandas to hold in memory while importing into the database so download the sas file directly
	scp  mywrdsusername@/wrds/crsp/sasdata/a_stock/dsf.sas7bdat 
	
9. Import the wrds data into the database ( from the project database dir )
	python database_import.py -p mydatabasepassword
	cd parquet
	scp mywrdsusername@wrds-cloud.wharton.upenn.edu: /wrds/crsp/sasdata/a_stock/dsf.sas7bdat .
	cd ..
	python dsf.py

10. download the S&P 500 index constiuents from here
	https://wrds-web.wharton.upenn.edu/wrds/ds/compd/index/constituents.cfm?navId=83
	select a date range of 2007-01-01 - 2018-12-31
	select GVKEYX,  company code: 000003
select all query variables
select an output format of csv
click submit query
click the csv link and put the csv file in the projects database/parquet directory
	rename the file as sp500.csv
	import the S&P 500 constituents into the database
	(from the project databse dir)
	python sp500.py
	
11. the following step limits the resultset in the database to the sp500 constiuents 
	export all sp500 views to file 
	
	dseall_sp500
	dsedelist_sp500
	dsedist_sp500
	dseexchdates_sp500
	dsenames_sp500
	dsenasdin_sp500
	dseshares_sp500
	dse_sp500
	dsfhdr_sp500
	dsf_sp500
	dsi_sp500
	dsiy_sp500
	stocknames_sp500
	
	from the project database dir
	using the following command on all views (ie - for dseall)
	psql -h myhost -p myport -U crsp crsp -c "copy dseall_sp500 to 'schema/dseall.csv'"
	psql -h myhost -p myport -U crsp crsp -c "truncate table dseall"
	psql -h myhost -p myport -U crsp crsp -c "copy dseall from 'schema/dseall.csv'"

12. create a dummy cash instrument
	from the projects database/schema dir
	psql -h myhost -p myport -U crsp crsp -f create_cash_instrument.sql
	
13. modify dash/config.py to point to your database installation

14. prepopulate the ticker metrics table by running the following scripts
	from the project database directory (this takes hours to run)

	python update_metrics_alpha.py  
	python update_metrics_beta.py
	python update_metrics_sharpe.py 
	python update_metrics_sortino.py 
	python update_metrics_volatility.py

15. run from the project dash dir
	flask run
	open a browser pointed at https://localhost:5000
