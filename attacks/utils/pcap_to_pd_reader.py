import pyshark
import pandas as pd

class pcap_reader:
    def load_pcapng_to_pd(self, path: str) -> pd.DataFrame:

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
        df_imd = self.add_imd_to_df(df)

        return df_imd

    def add_imd_to_df(self, df: pd.DataFrame) -> pd.DataFrame:
        for src_ip in df["Source IP"].unique():
            packets = df.query("`Source IP` == @src_ip")

            for rec_ip in packets["Destination IP"].unique():
                communication = packets.query("`Destination IP` == @rec_ip").sort_values(by=["Timestamp"])

                indices = communication.index
                previous_index = indices.to_list().pop(0)

                for index in indices:
                    df.at[index, "Inter-Message Delay"] = df.at[index, "Timestamp"] - df.at[previous_index, "Timestamp"]
                    previous_index = index

        return df