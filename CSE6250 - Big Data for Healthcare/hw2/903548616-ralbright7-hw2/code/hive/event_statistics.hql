-- ***************************************************************************
-- DO NOT modify the below provided framework and variable names/orders please
-- Loading Data:
-- create external table mapping for events.csv and mortality_events.csv

-- IMPORTANT NOTES:
-- You need to put events.csv and mortality.csv under hdfs directory 
-- '/input/events/events.csv' and '/input/mortality/mortality.csv'
-- 
-- To do this, run the following commands for events.csv, 
-- 1. sudo su - hdfs
-- 2. hdfs dfs -mkdir -p /input/events
-- 3. hdfs dfs -chown -R root /input
-- 4. exit 
-- 5. hdfs dfs -put /path-to-events.csv /input/events/
-- Follow the same steps 1 - 5 for mortality.csv, except that the path should be 
-- '/input/mortality'
-- ***************************************************************************
-- create events table 
DROP TABLE IF EXISTS events;
CREATE EXTERNAL TABLE events (
  patient_id STRING,
  event_id STRING,
  event_description STRING,
  time DATE,
  value DOUBLE)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/input/events';

-- create mortality events table 
DROP TABLE IF EXISTS mortality;
CREATE EXTERNAL TABLE mortality (
  patient_id STRING,
  time DATE,
  label INT)
ROW FORMAT DELIMITED FIELDS TERMINATED BY ','
STORED AS TEXTFILE
LOCATION '/input/mortality';


!echo "create view alive_events"; 
-- ******************************************************
-- Task 1:
-- By manipulating the above two tables, 
-- generate two views for alive and dead patients' events
-- ******************************************************
-- find events for alive patients
DROP VIEW IF EXISTS alive_events;
CREATE VIEW alive_events 
AS
SELECT events.patient_id, events.event_id, events.time 
-- ***** your code below *****
from events 
left join mortality m on events.patient_id = m.patient_id
where m.patient_id is null;

!echo "create view dead_events"; 
-- find events for dead patients
DROP VIEW IF EXISTS dead_events;
CREATE VIEW dead_events 
AS
SELECT events.patient_id, events.event_id, events.time
-- ***** your code below *****
from events
inner join mortality m on events.patient_id = m.patient_id;

!echo "event_count_alive"; 
-- ************************************************
-- Task 2: Event count metrics
-- Compute average, min and max of event counts 
-- for alive and dead patients respectively  
-- ************************************************
-- alive patients
INSERT OVERWRITE LOCAL DIRECTORY 'event_count_alive'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT avg(event_count), min(event_count), max(event_count)
-- ***** your code below *****
from (
    select patient_id, count(event_id) as event_count
    from alive_events
    group by patient_id
) q;

!echo "event_count_dead"; 
-- dead patients
INSERT OVERWRITE LOCAL DIRECTORY 'event_count_dead'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT avg(event_count), min(event_count), max(event_count)
-- ***** your code below *****
from (
  select patient_id, count(*) as event_count
  from dead_events
  group by patient_id
) q;


!echo "encounter_count_alive"; 
-- ************************************************
-- Task 3: Encounter count metrics 
-- Compute average, median, min and max of encounter counts 
-- for alive and dead patients respectively
-- ************************************************
-- alive
INSERT OVERWRITE LOCAL DIRECTORY 'encounter_count_alive'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT avg(encounter_count), percentile(encounter_count, 0.5), min(encounter_count), max(encounter_count)
-- ***** your code below *****
from (
  select patient_id, count(time) as encounter_count
  from (
    select patient_id, time
    from alive_events
    group by patient_id, time
  ) q1
  group by patient_id
) q2;

!echo "encounter_count_dead"; 
-- dead
INSERT OVERWRITE LOCAL DIRECTORY 'encounter_count_dead'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT avg(encounter_count), percentile(encounter_count, 0.5), min(encounter_count), max(encounter_count)
-- ***** your code below *****
from (
  select patient_id, count(time) as encounter_count
  from (
    select patient_id, time
    from dead_events
    group by patient_id, time
  ) q1
  group by patient_id
) q2;

!echo "record_length_alive"; 
-- ************************************************
-- Task 4: Record length metrics
-- Compute average, median, min and max of record lengths
-- for alive and dead patients respectively
-- ************************************************
-- alive 
INSERT OVERWRITE LOCAL DIRECTORY 'record_length_alive'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT avg(record_length), percentile(record_length, 0.5), min(record_length), max(record_length)
-- ***** your code below *****
from (
  select patient_id, datediff(max(time), min(time)) as record_length
  from alive_events
group by patient_id
) q;

!echo "record_length_dead"; 
-- dead
INSERT OVERWRITE LOCAL DIRECTORY 'record_length_dead'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT avg(record_length), percentile(record_length, 0.5), min(record_length), max(record_length)
-- ***** your code below *****
from (
  select patient_id, datediff(max(time), min(time)) as record_length
  from dead_events
group by patient_id
) q;

!echo "common_diag_alive";
-- ******************************************* 
-- Task 5: Common diag/lab/med
-- Compute the 5 most frequently occurring diag/lab/med
-- for alive and dead patients respectively
-- *******************************************
-- alive patients
---- diag
INSERT OVERWRITE LOCAL DIRECTORY 'common_diag_alive'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT event_id, count(*) AS diag_count
FROM alive_events
-- ***** your code below *****
where instr(event_id, 'DIAG') !=0
group by event_id
order by diag_count desc
limit 5;

!echo "common_lab_alive";
---- lab
INSERT OVERWRITE LOCAL DIRECTORY 'common_lab_alive'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT event_id, count(*) AS lab_count
FROM alive_events
-- ***** your code below *****
where instr(event_id, 'LAB') !=0
group by event_id
order by lab_count desc
limit 5;

!echo "common_med_alive";
---- med
INSERT OVERWRITE LOCAL DIRECTORY 'common_med_alive'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT event_id, count(*) AS med_count
FROM alive_events
-- ***** your code below *****
where instr(event_id, 'DRUG') !=0
group by event_id
order by med_count desc
limit 5;

!echo "common_diag_dead";
-- dead patients
---- diag
INSERT OVERWRITE LOCAL DIRECTORY 'common_diag_dead'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT event_id, count(*) AS diag_count
FROM dead_events
-- ***** your code below *****
where instr(event_id, 'DIAG') !=0
group by event_id
order by diag_count desc
limit 5;

!echo "common_lab_dead";
---- lab
INSERT OVERWRITE LOCAL DIRECTORY 'common_lab_dead'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT event_id, count(*) AS lab_count
FROM dead_events
-- ***** your code below *****
where instr(event_id, 'LAB') !=0
group by event_id
order by lab_count desc
limit 5;

!echo "common_med_dead";
---- med
INSERT OVERWRITE LOCAL DIRECTORY 'common_med_dead'
ROW FORMAT DELIMITED
FIELDS TERMINATED BY ','
STORED AS TEXTFILE
SELECT event_id, count(*) AS med_count
FROM dead_events
-- ***** your code below *****
where instr(event_id, 'DRUG') !=0
group by event_id
order by med_count desc
limit 5;
