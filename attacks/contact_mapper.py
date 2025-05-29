from re import T
import pandas as pd
from naive_sinkhorn_sda import naive_sinkhorn_sda
from simple_sda import simple_sda
from utils.user_table_with_alias import user_dataframe_dict_pair

def find_contacts(df: pd.DataFrame, target_ip: str, **kwargs) -> list[str]:
    common_contacts = []
    if len(kwargs) == 0 or 'length' not in kwargs.keys():
        return common_contacts
    length = kwargs['length']

    intermediate_lists = []
    if 'sinkhorn_filter' in kwargs.keys():
        sinkhorn = naive_sinkhorn_sda(df).to_dict()
        sinkhorn = dict(sorted(sinkhorn[target_ip].items(), key=lambda item: item[1]))
        keys = list(sinkhorn.keys())[::-1]
        
        intermediate_lists.append(keys[:length])    

    if 'simple_filter' in kwargs.keys():
        simple = simple_sda(df, 300, target_ip)
        simple_contacts = list(simple.keys())[::-1]

        intermediate_lists.append(simple_contacts[:length])
    

    # add any other attacks here

    #Finally, the intersection between all the different contact lists is found here
    common_contacts = intermediate_lists.pop()

    for contact_list in intermediate_lists:
        new_common_contacts = []
        for contact in common_contacts:
            if contact in contact_list:
                new_common_contacts.append(contact)
        
        common_contacts = new_common_contacts

    return common_contacts

if __name__ == '__main__':
    target_ip = "10.10.248.42" #Just an example, take the IP of the target user
    server_ip = "10.10.248.2"
    window_size = 1

    df = pd.read_csv("sim_files/output.csv")

    contacts = find_contacts(df, target_ip, sinkhorn_filter=True, simple_filter=True, length=5)
    table, di = user_dataframe_dict_pair()

    ids = []
    for contact in contacts:
        ids.append(di[contact])

    print(ids)