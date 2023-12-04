import time
import pandas as pd
import numpy as np

# PLEASE USE THE GIVEN FUNCTION NAME, DO NOT CHANGE IT

def read_csv(filepath):
    '''
    TODO : This function needs to be completed.
    Read the events.csv and mortality_events.csv files. 
    Variables returned from this function are passed as input to the metric functions.
    '''
    events = pd.read_csv(filepath + 'events.csv')
    mortality = pd.read_csv(filepath + 'mortality_events.csv')

    return events, mortality

def event_count_metrics(events, mortality):
    '''
    TODO : Implement this function to return the event count metrics.
    Event count is defined as the number of events recorded for a given patient.
    '''

    dead = mortality['patient_id'].unique()
    events_alive = events[~events['patient_id'].isin(dead)]
    events_dead = events[events['patient_id'].isin(dead)]
    alive_ct = events_alive[['patient_id', 'event_id']].groupby('patient_id').count()
    dead_ct = events_dead[['patient_id', 'event_id']].groupby('patient_id').count()

    avg_dead_event_count = dead_ct.mean().values[0]
    max_dead_event_count = dead_ct.max().values[0]
    min_dead_event_count = dead_ct.min().values[0]
    avg_alive_event_count = alive_ct.mean().values[0]
    max_alive_event_count = alive_ct.max().values[0]
    min_alive_event_count = alive_ct.min().values[0]

    return min_dead_event_count, max_dead_event_count, avg_dead_event_count, min_alive_event_count, max_alive_event_count, avg_alive_event_count

def encounter_count_metrics(events, mortality):
    '''
    TODO : Implement this function to return the encounter count metrics.
    Encounter count is defined as the count of unique dates on which a given patient visited the ICU. 
    '''
    dead = mortality['patient_id'].unique()
    events_alive = events[~events['patient_id'].isin(dead)]
    events_dead = events[events['patient_id'].isin(dead)]
    # DIAG, LAB and DRUG are encounters
    alive_diag = events_alive['event_id'].str.startswith('DIAG')
    alive_lab = events_alive['event_id'].str.startswith('LAB')
    alive_drug = events_alive['event_id'].str.startswith('DRUG')
    dead_diag = events_dead['event_id'].str.startswith('DIAG')
    dead_lab = events_dead['event_id'].str.startswith('LAB')
    dead_drug = events_dead['event_id'].str.startswith('DRUG')
    events_alive_enc = events_alive[(alive_diag) | (alive_lab) | (alive_drug)]
    events_dead_enc = events_dead[(dead_diag) | (dead_lab) | (dead_drug)]

    alive_ct = events_alive_enc.groupby('patient_id')['timestamp'].nunique().values
    dead_ct = events_dead_enc.groupby('patient_id')['timestamp'].nunique().values

    avg_dead_encounter_count = np.mean(dead_ct)
    max_dead_encounter_count = np.max(dead_ct)
    min_dead_encounter_count = np.min(dead_ct)
    avg_alive_encounter_count = np.mean(alive_ct)
    max_alive_encounter_count = np.max(alive_ct)
    min_alive_encounter_count = np.min(alive_ct)

    return min_dead_encounter_count, max_dead_encounter_count, avg_dead_encounter_count, min_alive_encounter_count, max_alive_encounter_count, avg_alive_encounter_count

def record_length_metrics(events, mortality):
    '''
    TODO: Implement this function to return the record length metrics.
    Record length is the duration between the first event and the last event for a given patient. 
    '''

    events['timestamp'] = pd.to_datetime(events['timestamp'])
    dead = mortality['patient_id'].unique()
    events_alive = events[~events['patient_id'].isin(dead)]
    events_dead = events[events['patient_id'].isin(dead)]
    alive_min = events_alive.groupby('patient_id')['timestamp'].min()
    alive_max = events_alive.groupby('patient_id')['timestamp'].max()
    dead_min = events_dead.groupby('patient_id')['timestamp'].min()
    dead_max = events_dead.groupby('patient_id')['timestamp'].max()

    alive_length = alive_max - alive_min
    dead_length = dead_max - dead_min.values

    avg_dead_rec_len = np.mean(dead_length.dt.days)
    max_dead_rec_len = np.max(dead_length.dt.days)
    min_dead_rec_len = np.min(dead_length.dt.days)
    avg_alive_rec_len = np.mean(alive_length.dt.days)
    max_alive_rec_len = np.max(alive_length.dt.days)
    min_alive_rec_len = np.min(alive_length.dt.days)

    return min_dead_rec_len, max_dead_rec_len, avg_dead_rec_len, min_alive_rec_len, max_alive_rec_len, avg_alive_rec_len

def main():
    '''
    DO NOT MODIFY THIS FUNCTION.
    '''
    # You may change the following path variable in coding but switch it back when submission.
    train_path = '../data/train/'

    # DO NOT CHANGE ANYTHING BELOW THIS ----------------------------
    events, mortality = read_csv(train_path)

    #Compute the event count metrics
    start_time = time.time()
    event_count = event_count_metrics(events, mortality)
    end_time = time.time()
    print(("Time to compute event count metrics: " + str(end_time - start_time) + "s"))
    print(event_count)

    #Compute the encounter count metrics
    start_time = time.time()
    encounter_count = encounter_count_metrics(events, mortality)
    end_time = time.time()
    print(("Time to compute encounter count metrics: " + str(end_time - start_time) + "s"))
    print(encounter_count)

    #Compute record length metrics
    start_time = time.time()
    record_length = record_length_metrics(events, mortality)
    end_time = time.time()
    print(("Time to compute record length metrics: " + str(end_time - start_time) + "s"))
    print(record_length)
    
if __name__ == "__main__":
    main()
