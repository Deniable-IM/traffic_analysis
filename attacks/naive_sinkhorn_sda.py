import pandas as pd
import pygmtools as pygm
from utils.user_table_with_alias import user_dataframe_dict_pair

pygm.set_backend("numpy")

def _update_senders(senders, time_delta):
    updated = []
    for sender, time in senders:
        remainding  = time - time_delta
        if remainding >= 0:
            updated.append((sender, remainding))

    return updated

def _update_receivers(senders, receiver_ip, matrix):
    receivers_in_senders = 0
    for sender, _ in senders:
        if sender == receiver_ip:
            receivers_in_senders += 1
            continue

        if sender not in matrix:
            matrix[sender] = dict()

        if receiver_ip not in matrix[sender]:
            matrix[sender][receiver_ip] = 0

        matrix[sender][receiver_ip] += 1 / (len(senders) - receivers_in_senders)
    
def naive_sinkhorn_sda(df: pd.DataFrame, server_ip = "10.10.248.2", window_size = 1) -> pd.DataFrame:
    df = df.sort_values(by='Time').set_index(df['Time'])
    df = df.query('Protocol == "TLSv1.3"')

    prev_time = df.iloc[0].Time
    senders = []
    receivers = dict(dict())
    # "No.","Time","Source","Destination","Protocol","Length","Info"
    for row in df.itertuples():
        senders = _update_senders(senders, row.Time - prev_time) #type: ignore
        
        if row.Destination in [server_ip]:
            senders.append((row.Source, window_size))
        else:
            _update_receivers(senders, row.Destination, receivers)

        prev_time = row.Time

    nn_matrix = pd.DataFrame.from_dict(receivers).fillna(0)
    res = pygm.sinkhorn(nn_matrix.to_numpy())
    return pd.DataFrame(res, index=nn_matrix.index, columns=nn_matrix.columns)

if __name__ == '__main__':
    target_ip = "10.10.253.236" #Just an example, take the IP of the target user
    server_ip = "10.10.248.2"
    window_size = 1

    df = pd.read_csv("sim_files/output.csv")
    probs = naive_sinkhorn_sda(df, server_ip=server_ip, window_size=window_size).to_dict()

    user_table, ip_to_id_map = user_dataframe_dict_pair()

    target_contact_list = user_table.query('UserIP == @target_ip')['RegularContactList'].tolist().pop()

    sorted_dict = dict(sorted(probs[target_ip].items(), key=lambda item: item[1]))
    for k, v in sorted_dict.items():
        id = ip_to_id_map[k]    
        if id in target_contact_list:
            print(f'{id} : {v} <-- Is a contact')
        else:
            print(f'{id} : {v}')