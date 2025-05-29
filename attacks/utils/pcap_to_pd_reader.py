import pyshark
import pandas as pd

def load_pcapng_to_pd(  path: str) -> pd.DataFrame:

    cap = pyshark.FileCapture(path)
    cap.keep_packets = False
    data = []

    for packet in cap:
        if 'IP' in packet and 'TCP' in packet:
            data.append({
                "Packet Number": packet.number,
                "Timestamp": packet.sniff_time,
                "Length": packet.length,
                "Source IP": packet.ip.src,
                "Destination IP": packet.ip.dst,
                "Source Port": packet.tcp.srcport,
                "Destination Port": packet.tcp.dstport,
                "Inter-Message Delay": pd.NaT
            })

    cap.close()

    df = pd.DataFrame(data)
    # df_imd = self.add_imd_to_df(df)

    return df
# "No.","Time","Source","Destination","Protocol","Length","Info"

def add_imd_to_df(df: pd.DataFrame) -> pd.DataFrame:
    for src_ip in df['Source'].unique().tolist():
        packets = df.query('Source == @src_ip').sort_values(by=['Time'])
        packets['IMD'] = packets['Time'].diff()

        for index in packets['IMD'].index:
            df.at[index, 'IMD'] = packets.at[index, 'IMD']
        


    return df