import psycopg2

conn = psycopg2.connect(
    host='database-1.cudz1l7w5ie2.us-east-1.rds.amazonaws.com',
    port=5432,
    user='crsp',
    password='crspcse6242',
    database='crsp')
cursor = conn.cursor()
sql = """
    select permno 
    from dsf
    group by permno
    order by permno
    """

cursor.execute(sql)
res = cursor.fetchall()
permnos = []
for row in res:
    permnos.append(row[0])

sql = "select update_metrics_sharpe(%s::integer)"
i = 1
for permno in permnos:
    cursor.execute(sql, [permno])
    conn.commit()
    print("%s: %s" %  (i, permno))
    i+=1

