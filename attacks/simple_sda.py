from random import randint
import pandas as pd
from utils.user_table_with_alias import user_dataframe_dict_pair

def simple_sda(df: pd.DataFrame, rounds, target_ip, server_ip = "10.10.248.2", window_size = 1):
    df = df.sort_values(by='Time').set_index(df['Time'])
    df = df.query('Protocol == "TLSv1.3"')
    df_target = df.query('Source == @target_ip')
    rounds = min(rounds, df_target['Time'].size)

    suspect_table = dict()
    for user in df["Source"].unique().tolist():
        if user not in [target_ip, server_ip]:
            suspect_table[user] = 0
        
    for i in range(0, rounds):    
        #Target epoch
        r_target = randint(0, (len(df_target.index) - 1))
        target_time_start = df_target.iloc[r_target].at['Time']
        target_time_end = target_time_start + window_size

        target_epoch = df.query('Time > @target_time_start and Time <= @target_time_end and Source != @server_ip')
        for x in target_epoch['Source']:
            if x == target_ip:
                continue
            suspect_table[x] += 1
        
        #Random epoch
        r_random = randint(0, len(df.index) - 1)
        random_time_start = df.iloc[r_random].at['Time']
        random_time_end = random_time_start + window_size

        random_epoch = df.query('Time > @random_time_start and Time <= @random_time_end and Source != @server_ip')
        for x in random_epoch['Source']:
            if x == target_ip:
                continue
            suspect_table[x] -= 1

    return dict(sorted(suspect_table.items(), key=lambda item: item[1]))



if __name__ == '__main__':
    target_ip = "10.10.249.103" #Just an example, take the IP of the target user
    window_size = 1
    rounds = 500

    df = pd.read_csv("sim_files/output.csv")
    
    suspect_table = simple_sda(df, rounds, target_ip, window_size=window_size)

    user_table, ip_to_id_map = user_dataframe_dict_pair()

    target_contact_list = user_table.query('UserIP == @target_ip')['RegularContactList'].tolist().pop()
    print("All users")
    print("ID : Score")
    sorted_dict = dict(sorted(suspect_table.items(), key=lambda item: item[1]))
    for k, v in sorted_dict.items():
        id = ip_to_id_map[k]    
        if id in target_contact_list:
            print(f'{id} : {v} <-- Is a contact')
        else:
            print(f'{id} : {v}')

