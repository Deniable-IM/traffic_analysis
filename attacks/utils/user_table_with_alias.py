import pandas as pd

def user_dataframe_dict_pair() -> tuple[pd.DataFrame, dict[str, str]]:
    user_table = pd.read_json("sim_files/users.json")
    user_table = user_table.merge(pd.DataFrame().from_records(user_table['User']), left_index=True, right_index=True)
    user_table = user_table.drop(columns=['User'])
    user_table = user_table.merge(pd.DataFrame().from_records(user_table['Behavior']), left_index=True, right_index=True)
    user_table = user_table.drop(columns=['Behavior'])

    # Purely for cosmetic purposes
    ip_to_id_map = dict()
    for i in user_table.index.to_list():
        ip = user_table.at[i, 'UserIP']
        id = user_table.at[i, 'ID']
        ip_to_id_map[ip] = str(id)

    return (user_table, ip_to_id_map)
