insert into stocknames(permno, permco, namedt, nameenddt, ticker, comnam, st_date, end_date)
values(0, 0, '2007-01-01', '2018-12-31', 'CASH', 'CASH Instrument', '2007-01-01', '2018-12-31');

insert into dsf(date, permco, permno, prc, cfacpr, cfacshr)
select date, 0, 0 as permno, 1 as prc, 1 as cfacpr, 1 as cfacshr
from market_tradedays 
where date >='2003-12-31' and date <='2018-12-31' 
order by date;
