from http import server
import pandas as pd
import pygmtools as pygm
from utils.user_table_with_alias import user_dataframe_dict_pair, new_user_dataframe_dict_pair
from deniable_spotter import find_deniable_sequences
from tqdm import tqdm

pygm.set_backend("numpy")

def _update_senders(senders, time_delta):
    updated = []
    for sender, no, last, time in senders:
        remaining  = time - time_delta
        if remaining > 0:
            updated.append((sender, no, last, remaining))

    return updated

def _update_receivers(senders, receiver_ip, matrix):
    receiver_in_senders = 0
    for sender in senders:
        if sender == receiver_ip:
            receiver_in_senders += 1

    for sender in senders:
        if sender == receiver_ip:
            continue

        if sender not in matrix:
            matrix[sender] = dict()

        if receiver_ip not in matrix[sender]:
            matrix[sender][receiver_ip] = 0

        matrix[sender][receiver_ip] += 1 / (len(senders) - receiver_in_senders)
    
def deniable_sinkhorn_sda(df: pd.DataFrame, server_ip = "10.10.248.2", window_size = 100.0) -> pd.DataFrame:
    df = df.sort_values(by='Time')#.set_index(df['Time'])
    df = df.query('Protocol == "TLSv1.3"')
    deniable_df = find_deniable_sequences(df, imd_filter=1, burst_len=3, server_ip=server_ip)
    print(f'df len = {df.shape[0]}')
    print(f'den df len = {deniable_df.shape[0]}')
    # user_df = deniable_df.query('Source != @server_ip')
    # deniable_df = deniable_df.query('IsBurst == True and Source != @server_ip')    

    prev_time = df.iloc[0].Time
    senders = []
    receivers = dict(dict())
    burst_tracker = dict([])
    last_received = dict()
    debug_update_receiver_count = 0
    # "No.","Time","Source","Destination","Protocol","Length","Info"
    for row in tqdm(deniable_df.itertuples(), total=deniable_df.shape[0]):
        senders = _update_senders(senders, row.Time - prev_time) #type: ignore

        if row.Source == server_ip:
            last_received[row.Destination] = row.Time
            continue

        if row.IsBurst == True: # == True is necessary because of fucking course it is
            if row.BurstNo not in burst_tracker.keys():
                burst_tracker[row.BurstNo] = [row.Index]
                if row.Source in last_received.keys():
                    #update receivers, but filter unviable senders
                    viable_senders = []
                    for source, _, time, _ in senders:
                        if time < last_received[row.Source]:
                            viable_senders.append(source)

                    debug_update_receiver_count += 1
                    _update_receivers(viable_senders, row.Source, receivers)
                else:
                    viable_senders = []
                    for source, _, _, _ in senders:
                        viable_senders.append(source)
                    _update_receivers(viable_senders, row.Source, receivers)
                
            else:
                burst_tracker[row.BurstNo].append(row.Index)

            if row.IsLast == True: # == True is necessary because of fucking course it is
                senders.append((row.Source, row.BurstNo, row.Time, window_size))

        prev_time = row.Time

    nn_matrix = pd.DataFrame.from_dict(receivers).fillna(0)
    print(f'Update receivers called {debug_update_receiver_count} times')
    res = pygm.sinkhorn(nn_matrix.to_numpy())
    return pd.DataFrame(res, index=nn_matrix.index, columns=nn_matrix.columns)

if __name__ == '__main__':
    target_ip = "10.10.249.226" #Just an example, take the IP of the target user
    server_ip = "10.10.248.2"
    window_size = 90

    df = pd.read_csv("sim_files/output.csv")
    
    probs = deniable_sinkhorn_sda(df, server_ip=server_ip, window_size=window_size).to_dict()



    user_table, ip_to_id_map = user_dataframe_dict_pair()


    target_user = user_table.query('UserIP == @target_ip')
    target_deniable_contacts = target_user['DeniableContactList'].tolist().pop()
    regular_deniable_contacts = target_user['RegularContactList'].tolist().pop()

    sorted_dict = dict(sorted(probs[target_ip].items(), key=lambda item: item[1]))
    for k, v in sorted_dict.items():
        id = ip_to_id_map[k]    
        if id in target_deniable_contacts:
            print(f'{id} : {v} <-- Deniable contact')
        elif id in regular_deniable_contacts:
            print(f'{id} : {v} <-- Regular contact')
        else:
            print(f'{id} : {v}')