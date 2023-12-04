import utils
import pandas as pd

# PLEASE USE THE GIVEN FUNCTION NAME, DO NOT CHANGE IT

def read_csv(filepath):
    
    '''
    TODO: This function needs to be completed.
    Read the events.csv, mortality_events.csv and event_feature_map.csv files into events, mortality and feature_map.
    
    Return events, mortality and feature_map
    '''

    #Columns in events.csv - patient_id,event_id,event_description,timestamp,value
    events = pd.read_csv(filepath + 'events.csv', parse_dates=['timestamp'])
    
    #Columns in mortality_event.csv - patient_id,timestamp,label
    mortality = pd.read_csv(filepath + 'mortality_events.csv', parse_dates=['timestamp'])

    #Columns in event_feature_map.csv - idx,event_id
    feature_map = pd.read_csv(filepath + 'event_feature_map.csv')

    return events, mortality, feature_map


def calculate_index_date(events, mortality, deliverables_path):
    
    '''
    TODO: This function needs to be completed.

    Refer to instructions in Q3 a

    Suggested steps:
    1. Create list of patients alive ( mortality_events.csv only contains information about patients deceased)
    2. Split events into two groups based on whether the patient is alive or deceased
    3. Calculate index date for each patient
    
    IMPORTANT:
    Save indx_date to a csv file in the deliverables folder named as etl_index_dates.csv. 
    Use the global variable deliverables_path while specifying the filepath. 
    Each row is of the form patient_id, indx_date.
    The csv file should have a header 
    For example if you are using Pandas, you could write: 
        indx_date.to_csv(deliverables_path + 'etl_index_dates.csv', columns=['patient_id', 'indx_date'], index=False)

    Return indx_date
    '''
    dead = mortality['patient_id'][mortality['label']==1]
    events_alive = events[~events['patient_id'].isin(dead)].copy()

    alive_max = events_alive.groupby('patient_id')['timestamp'].max()
    alive_max = alive_max.to_frame()
    alive_max = alive_max.reset_index()
    alive_max['indx_date'] = alive_max['timestamp']

    dead_max = mortality[['patient_id', 'timestamp']]
    dead_max['indx_date'] = dead_max['timestamp'] - pd.to_timedelta(30, unit='d')

    indx_date = pd.concat([dead_max, alive_max])
    indx_date.reset_index(inplace=True)
    indx_date.drop(columns=['index', 'timestamp'], inplace=True)
    indx_date.sort_values(by=['patient_id'], inplace=True)
    indx_date.to_csv(deliverables_path + 'etl_index_dates.csv', columns=['patient_id', 'indx_date'], index=False)
    return indx_date


def filter_events(events, indx_date, deliverables_path):
    
    '''
    TODO: This function needs to be completed.

    Refer to instructions in Q3 b

    Suggested steps:
    1. Join indx_date with events on patient_id
    2. Filter events occuring in the observation window(IndexDate-2000 to IndexDate)
    
    
    IMPORTANT:
    Save filtered_events to a csv file in the deliverables folder named as etl_filtered_events.csv. 
    Use the global variable deliverables_path while specifying the filepath. 
    Each row is of the form patient_id, event_id, value.
    The csv file should have a header 
    For example if you are using Pandas, you could write: 
        filtered_events.to_csv(deliverables_path + 'etl_filtered_events.csv', columns=['patient_id', 'event_id', 'value'], index=False)

    Return filtered_events
    '''

    events = pd.merge(events, indx_date, how='inner', on='patient_id')
    events['begin'] = events['indx_date'] - pd.to_timedelta(2000, unit='d')
    filtered_events = events[(events['timestamp'] >= events['begin']) & (events['timestamp'] <= events['indx_date'])]
    filtered_events.to_csv(deliverables_path + 'etl_filtered_events.csv', columns=['patient_id', 'event_id', 'value'], index=False)
    filtered_events = filtered_events[['patient_id', 'event_id', 'value']]
    return filtered_events


def aggregate_events(filtered_events_df, mortality_df,feature_map_df, deliverables_path):
    
    '''
    TODO: This function needs to be completed.

    Refer to instructions in Q3 c

    Suggested steps:
    1. Replace event_id's with index available in event_feature_map.csv
    2. Remove events with n/a values
    3. Aggregate events using sum and count to calculate feature value
    4. Normalize the values obtained above using min-max normalization(the min value will be 0 in all scenarios)
    
    
    IMPORTANT:
    Save aggregated_events to a csv file in the deliverables folder named as etl_aggregated_events.csv. 
    Use the global variable deliverables_path while specifying the filepath. 
    Each row is of the form patient_id, event_id, value.
    The csv file should have a header .
    For example if you are using Pandas, you could write: 
        aggregated_events.to_csv(deliverables_path + 'etl_aggregated_events.csv', columns=['patient_id', 'feature_id', 'feature_value'], index=False)

    Return filtered_events
    '''
    filtered_events_df = pd.merge(filtered_events_df, feature_map_df, how='inner', on='event_id')
    filtered_events_df = filtered_events_df.dropna(subset=['value'])
    filtered_events_df.rename(columns={'idx': 'feature_id', 'value': 'feature_value'}, inplace=True)
    filtered_events_df['event_type'] = None

    for t in ['DIAG', 'DRUG', 'LAB']:
        filtered_events_df.loc[filtered_events_df['event_id'].str.startswith(t), 'event_type'] = t

    diag_drug = filtered_events_df[(filtered_events_df['event_type']=='DIAG') | (filtered_events_df['event_type'] == 'DRUG')]
    lab = filtered_events_df[filtered_events_df['event_type']=='LAB']
    diag_drug_agg = diag_drug[['patient_id', 'feature_id', 'feature_value']].groupby(['patient_id', 'feature_id']).sum()
    diag_drug_agg.reset_index(inplace=True)

    lab_agg = lab[['patient_id', 'feature_id', 'feature_value']].groupby(['patient_id', 'feature_id']).count()
    lab_agg.reset_index(inplace=True)

    aggregated_events = pd.concat([diag_drug_agg, lab_agg])
    max_events = aggregated_events[['feature_id', 'feature_value']].groupby(['feature_id']).max()
    max_events.reset_index(inplace=True)
    max_events.rename(columns={'feature_value':'max_value'}, inplace=True)
    aggregated_events = pd.merge(aggregated_events, max_events, how='inner', on=['feature_id'])
    aggregated_events['feature_value'] = aggregated_events['feature_value'] / aggregated_events['max_value']
    aggregated_events.sort_values(by=['patient_id', 'feature_id'], inplace=True)
    aggregated_events.to_csv(deliverables_path + 'etl_aggregated_events.csv', columns=['patient_id', 'feature_id', 'feature_value'], index=False)
    return aggregated_events

def create_features(events, mortality, feature_map):
    
    deliverables_path = '../deliverables/'

    #Calculate index date
    indx_date = calculate_index_date(events, mortality, deliverables_path)

    #Filter events in the observation window
    filtered_events = filter_events(events, indx_date,  deliverables_path)
    
    #Aggregate the event values for each patient 
    aggregated_events = aggregate_events(filtered_events, mortality, feature_map, deliverables_path)

    '''
    TODO: Complete the code below by creating two dictionaries - 
    1. patient_features :  Key - patient_id and value is array of tuples(feature_id, feature_value)
    2. mortality : Key - patient_id and value is mortality label
    '''

    aggregated_events.sort_values(by=['patient_id', 'feature_id'], inplace=True)
    patient_features = {}
    for row in aggregated_events.itertuples():
        row = row._asdict()
        if patient_features.get(row['patient_id']) is None:
            patient_features[row['patient_id']] = [(row['feature_id'], row['feature_value'])]
        else:
            patient_features[row['patient_id']].append((row['feature_id'], row['feature_value']))
    
    mort = {}
    for row in mortality.itertuples():
        row = row._asdict()
        if mort.get(row['patient_id']) is None:
            mort[row['patient_id']] = row['label']
    # we need to add in patients that are alive
    for row in aggregated_events.itertuples():
        row = row._asdict()
        if mort.get(row['patient_id']) is None:
            mort[row['patient_id']] = 0

    return patient_features, mort

def save_svmlight(patient_features, mortality, op_file, op_deliverable):
    
    '''
    TODO: This function needs to be completed

    Refer to instructions in Q3 d

    Create two files:
    1. op_file - which saves the features in svmlight format. (See instructions in Q3d for detailed explanation)
    2. op_deliverable - which saves the features in following format:
       patient_id1 label feature_id:feature_value feature_id:feature_value feature_id:feature_value ...
       patient_id2 label feature_id:feature_value feature_id:feature_value feature_id:feature_value ...  
    
    Note: Please make sure the features are ordered in ascending order, and patients are stored in ascending order as well.     
    '''
    op_file_arr = []
    op_deliverable_arr = []
    for key in mortality:
        line = [f"{mortality[key]}"]
        if patient_features.get(key) is not None:
            vals = [":".join(
                [f"{int(tup[0])}", f"{tup[1]:.6f}"]) 
                for tup in sorted(patient_features[key], key=lambda x: x[0])]
            line_arr = line + vals
            ln = " ".join(line_arr)
            op_file_arr.append(ln)
            del_ln = " ".join([str(int(key)), ln])
            op_deliverable_arr.append(del_ln)
    
    op_file_contents = " \n".join(op_file_arr)
    op_deliverable_contents = " \n".join(op_deliverable_arr)
    op_file_contents += " \n"
    op_deliverable_contents += " \n"

    deliverable1 = open(op_file, 'wb')
    deliverable2 = open(op_deliverable, 'wb')
    
    deliverable1.write(bytes(op_file_contents, 'UTF-8')) #Use 'UTF-8'
    deliverable2.write(bytes(op_deliverable_contents, 'UTF-8'))

def main():
    train_path = '../data/train/'
    events, mortality, feature_map = read_csv(train_path)
    patient_features, mortality = create_features(events, mortality, feature_map)
    save_svmlight(patient_features, mortality, '../deliverables/features_svmlight.train', '../deliverables/features.train')

if __name__ == "__main__":
    main()