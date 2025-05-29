import numpy as np
import pandas as pd 
import math

from random import randint 
from tqdm import tqdm
from utils.user_table_with_alias import user_dataframe_dict_pair
from utils.pcap_to_pd_reader import add_imd_to_df

def find_deniable_sequences(df: pd.DataFrame, imd_filter = 0.1, burst_len = 7, server_ip = "10.10.248.2") -> pd.DataFrame:
    df = add_imd_to_df(df)
    user_traffic = df.query('Source != @server_ip')
    burst_no = 0

    for user in user_traffic['Source'].unique().tolist():
        user_df = user_traffic.query('Source == @user')
        temp_list = []
        for row in user_df.itertuples():
            if math.isnan(row.IMD): #type: ignore #sut mig, python typesystem
                continue 

            if row.IMD < imd_filter: #type: ignore #Me when I make a type system so bad that people need to tell it to STFU
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
    return df

def naive_find_deniable_contacts(df: pd.DataFrame, target_ip, window_size, iterations):
    target_sequences = df.query('Source == @target_ip')
    target_end_times = []
    print(f'Total of {len(target_sequences['BurstNo'].unique())} deniable sequences from target')
    for BurstId in target_sequences['BurstNo'].unique().tolist():
        burst = df.query('BurstNo == @BurstId')
        target_end_times.append(burst['Time'].max())


    suspects = dict()
    suspect_burst_start_time = dict()
    suspect_burst_end_time = dict()

    suspect_traffic = df.query('Source != @target_ip')
    for src in suspect_traffic['Source'].unique().tolist():
        suspects[src] = 0
    
    for no in suspect_traffic['BurstNo'].unique().tolist():
        burst = df.query('BurstNo == @no')
        suspect_burst_start_time[no] = (burst.iloc[0].at['Source'], burst['Time'].min())
        suspect_burst_end_time[no] = (burst.iloc[0].at['Source'], burst['Time'].max())

    for i in tqdm(range(0, iterations)):
        #Target epoch
        target_epoch_start = target_end_times[randint(0, len(target_end_times) - 1)]
        target_epoch_end = target_epoch_start + window_size

        for k, (sender, time) in suspect_burst_start_time.items():
            if time >= target_epoch_start and time <= target_epoch_end:
                suspects[sender] += 1

        random_epoch_start = df.iloc[randint(0, (df.shape[0] - 1))].at['Time']
        random_epoch_end = random_epoch_start + window_size

        for k, (sender, time) in suspect_burst_start_time.items():
            if time >= random_epoch_start and time <= random_epoch_end:
                suspects[sender] -= 1


    #Legacy code
    # for time in target_end_times:
    #     window_start = time + offset
    #     window_end = window_start + window_size
    #     remain_list = []
    #     deniable_window = suspect_traffic.query('Time >= @ window_start and Time <= @window_end')

    #     for row in deniable_window.itertuples():
    #         if row.Time != suspect_burst_start_time[row.BurstNo]:
    #             continue
            
    #         remain_list.append(row.Source)
    #         suspects[row.Source] += 1

    #     for src in suspect_traffic['Source'].unique().tolist():
    #         if src in remain_list:
    #             continue
    #         # suspects[src] -= 1

    return suspects


if __name__ == '__main__':
    server_ip = "10.10.248.2"
    target_ip = "10.10.249.226"

    df = pd.read_csv("sim_files/output.csv")
    df = df.query('Protocol == "TLSv1.3"')
    df = find_deniable_sequences(df, imd_filter=1, burst_len=4)
    user_df = df.query('Source != @server_ip')
    df = user_df.query('IsBurst == True')

    suspects = naive_find_deniable_contacts(df, target_ip, 90, 200)
    
    regular_contacts = []
    for contact in regular_contacts:
        del suspects[contact]


    user_table, ip_to_id_map = user_dataframe_dict_pair()

    
    target_user = user_table.query('UserIP == @target_ip')
    target_deniable_contacts = target_user['DeniableContactList'].tolist().pop()
    target_regular_contacts = target_user['RegularContactList'].tolist().pop()

    print("All users")
    print("ID : Score")
    sorted_dict = dict(sorted(suspects.items(), key=lambda item: item[1]))
    for k, v in sorted_dict.items():
        id = ip_to_id_map[k]    
        if id in target_deniable_contacts:
            print(f'{id} : {v} <-- Deniable contact')
        elif id in target_regular_contacts:
            print(f'{id} : {v} <-- Regular contact')
        else:
            print(f'{id} : {v}')

    # print(df)
    # print(f'Burst packets = {df.shape[0]}')
    # print(f'Number of bursts = {len(df['BurstNo'].unique().tolist())}')
    # print(f'BurstLen description')
    # print(df['BurstLen'].describe())
