import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json





if __name__ == "__main__":
    df = pd.read_json("sim_validator/sim_outputs/messages.json")
    df2 = pd.DataFrame.from_records(df['Msg'])
    df = df.merge(df2, left_index=True, right_index=True)
    df = df.drop(columns=['Msg'])

    for sender in df['From'].unique():
        msgs = df.query("From == @sender and EventType == 'Send'")
        imds = msgs['Timestamp'].diff()
        for index in imds.index:
            df.at[index, 'IMD'] = pd.Timedelta(imds[index]).total_seconds()
    
    df = df.dropna()
    print(df)
    print(df.dtypes)

    df = df.query('From == "36" or From == "91"')

    senders = df['From'].unique()
    sender_count = senders.size
    vheight = sender_count * 2

    fig, axs = plt.subplots(sender_count, sharex=True, figsize=(8, vheight))

    for ax, sender in zip(axs, senders, strict=True):
        to_plot = df.query("From == @sender")['IMD']
        ax.set_title(f'User {sender}')
        bin_count = 0
        if to_plot.unique().size >= 100:
            bin_count = int(to_plot.unique().size / 8)
        else:
            bin_count = int(to_plot.unique().size / 2)
        ax.hist(to_plot, bins=bin_count, edgecolor='blue', alpha=0.7, density=True)
        time_deltas = to_plot
        x = np.linspace(min(time_deltas), max(time_deltas), 100)
        lambda_param = np.log(2) / time_deltas.median()
        lambda_param = 1 / time_deltas.mean()
        pdf = lambda_param * np.exp(-lambda_param * x)
        # cdf = 1 - np.exp(-lambda_param * x)
        # positive_half_laplace = (1 / 2 * b) * np.exp(- (abs(x - mu) / b))

        ax.plot(x, pdf, 'r', linewidth=2)




    # time_deltas = df['IMD']
    # plt.hist(time_deltas, bins=60, edgecolor='blue', alpha=0.7, density=True,)
    # # x = np.linspace(min(time_deltas), max(time_deltas), 100)

    # plt.xlabel('Inter-Message Delay (Seconds)')
    # plt.ylabel('Frequency')
    # plt.title('Histogram of Inter-Message Delay (Seconds)')
    # plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show Plot
    plt.tight_layout()
    plt.savefig(f"plots/{datetime.datetime.now()}.png", format="png", dpi=300, bbox_inches="tight")
    # plt.show()