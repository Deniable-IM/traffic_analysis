import numpy as np
import pandas as pd 
import math
import os
import pickle

from random import randint, choice 
from tqdm import tqdm
from utils.user_table_with_alias import user_dataframe_dict_pair
from utils.pcap_to_pd_reader import add_imd_to_df

def find_deniable_sequences(df: pd.DataFrame, imd_filter = 0.1, burst_len = 7, server_ip = "10.10.248.2") -> pd.DataFrame:
    if os.path.exists('sim_files/output.pkl'):
        return pd.read_pickle('sim_files/output.pkl')
    
    df = add_imd_to_df(df)
    user_traffic = df.query('Source != @server_ip')
    burst_no = 0

    for user in tqdm(user_traffic['Source'].unique().tolist()):
        user_df = user_traffic.query('Source == @user')
        temp_list = []
        for row in user_df.itertuples():
            if math.isnan(row.IMD): #type: ignore #sut mig, python typesystem
                continue 

            if row.IMD <= imd_filter: #type: ignore #Me when I make a type system so bad that people need to tell it to STFU
                temp_list.append(row.Index)
            else:
                temp_len = len(temp_list) 
                if temp_len >= burst_len:
                    i = temp_list[0]
                    for index in temp_list:
                        df.at[index, 'IsBurst'] = True
                        df.at[index, 'BurstNo'] = burst_no
                        df.at[index, 'BurstLen'] = temp_len
                        df.at[index, 'IsLast'] = False
                        i = index
                    temp_list = []
                    burst_no += 1
                    df.at[i, 'IsLast'] = True
                else:
                    temp_list = []
    print(f'Found {burst_no} deniable sequences')

    df.to_pickle('sim_files/output.pkl')


    return df

def naive_find_deniable_contacts(df: pd.DataFrame, target_ip, server_ip, window_size, iterations, viable_prune=False):
    user_df = df.query('Source != @server_ip and IsBurst == True')
    target_sequences = user_df.query('Source == @target_ip')
    target_end_times = []
    print(f'Total of {len(target_sequences['BurstNo'].unique())} deniable sequences from target')

    suspects = dict()
    suspect_burst_start_time = dict()
    suspect_burst_end_time = dict()

    suspect_traffic = user_df.query('Source != @target_ip')
    for src in suspect_traffic['Source'].unique().tolist():
        suspects[src] = 0
    
    if os.path.exists('sim_files/intermidate_data.pkl'):
        with open('sim_files/intermidate_data.pkl', 'rb') as f:
            print('Reading intermediate files...')
            target_end_times, suspect_burst_start_time, suspect_burst_end_time = pickle.load(f)
    else:
        print('No intermediate files found, generating new...')
        for BurstId in target_sequences['BurstNo'].unique().tolist():
            burst = user_df.query('BurstNo == @BurstId')
            target_end_times.append(burst['Time'].max())

        for no in tqdm(suspect_traffic['BurstNo'].unique().tolist()):
            burst = user_df.query('BurstNo == @no')
            suspect_burst_start_time[no] = (burst.iloc[0].at['Source'], burst['Time'].min())
            suspect_burst_end_time[no] = (burst.iloc[0].at['Source'], burst['Time'].max())

        
        with open('sim_files/intermidate_data.pkl', 'wb') as f:
            pickle.dump((target_end_times, suspect_burst_start_time, suspect_burst_end_time), f)

    

    for i in tqdm(range(0, iterations)):
        #Target epoch
        target_epoch_start = choice(target_end_times)
        target_epoch_end = target_epoch_start + window_size

        if viable_prune:
            target_data = df.query('Time >= @target_epoch_start and Time <= @target_epoch_end and Source != @server_ip')
            earliest_recv_time = dict()
            
            for row in target_data.itertuples():
                if row.Source not in earliest_recv_time.keys():
                    earliest_recv_time[row.Source] = row.Time
            for k, (sender, time) in suspect_burst_start_time.items():
                if time >= target_epoch_start and time <= target_epoch_end and time > earliest_recv_time[sender]:
                    suspects[sender] += 1
            
        else:
            for k, (sender, time) in suspect_burst_start_time.items():
                if time >= target_epoch_start and time <= target_epoch_end:
                    suspects[sender] += 1



        _, random_epoch_start = choice(list(suspect_burst_end_time.values()))
        random_epoch_end = random_epoch_start + window_size

        for k, (sender, time) in suspect_burst_start_time.items():
            if time >= random_epoch_start and time <= random_epoch_end:
                suspects[sender] -= 1

    return suspects


if __name__ == '__main__':
    server_ip = "10.10.248.2"
    target_ip = "10.10.254.234"

    df = pd.read_csv("sim_files/output.csv")
    df = df.query('Protocol == "TLSv1.2"')
    df = find_deniable_sequences(df, imd_filter=1, burst_len=4)
    

    regular_prune = True

    suspects = naive_find_deniable_contacts(df, target_ip, server_ip, 105, 300, viable_prune=True)
    
    regular_contacts = []
    for contact in regular_contacts:
        del suspects[contact]

    user_table, ip_to_id_map = user_dataframe_dict_pair()
    
    target_user = user_table.query('UserIP == @target_ip')
    target_deniable_contacts = target_user['DeniableContactList'].tolist().pop()
    target_regular_contacts = target_user['RegularContactList'].tolist().pop()
    remove_list = []
    for k, v in suspects.items():
        if regular_prune:
            if ip_to_id_map[k] in target_regular_contacts:
                remove_list.append(k)
        # if v < 0 and k not in remove_list:
        #     remove_list.append(k)

    for elem in remove_list:
        del suspects[elem]

    # normalization_factor = sum(suspects.values())
    # for k in suspects.keys():
        # suspects[k] /= normalization_factor

    contact_count = len(suspects.keys())
    print("All users")
    print("ID : Score")
    sorted_dict = dict(sorted(suspects.items(), key=lambda item: item[1]))
    for k, v in sorted_dict.items():
        id = ip_to_id_map[k]    
        if id in target_deniable_contacts:
            print(f'({contact_count}): {id} : {v} <-- Deniable contact')
        elif id in target_regular_contacts:
            print(f'({contact_count}): {id} : {v} <-- Regular contact')
        else:
            print(f'({contact_count}): {id} : {v}')
        contact_count -= 1

    # print(df)
    # print(f'Burst packets = {df.shape[0]}')
    # print(f'Number of bursts = {len(df['BurstNo'].unique().tolist())}')
    # print(f'BurstLen description')
    # print(df['BurstLen'].describe())
