import pyshark
import pandas as pd

class pcap_reader:
    def load_pcapng_to_pd(path: str) -> pd.DataFrame:

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
                    "Destination Port": packet.tcp.dstport
                })

        cap.close()



        return pd.DataFrame(data)
    
    def add_imd_to_df(df: pd.DataFrame) -> pd.DataFrame:


        pass