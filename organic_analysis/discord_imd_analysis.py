import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

def read_json_files():
    f = open("organic_analysis/IM_files/DM_IDs.txt")
    dirlist = []
    for dir_name in f:
        filename = f"messages/{dir_name.rstrip('\n')}/messages.json"
        dirlist.append(filename)

    path = dirlist.pop(0)
    file_path = f"organic_analysis/IM_files/{path}"
    df = pd.read_json(file_path)
    df = df.sort_values(by=["Timestamp"]).reset_index(drop=True)
    df['IMD'] = df['Timestamp'].diff()

    for file in dirlist:
        df1 = df
        file_path = f"organic_analysis/IM_files/{file}"
        df2 = pd.read_json(file_path)
        df2 = df2.sort_values(by=["Timestamp"]).reset_index(drop=True)

        # df2['IMD'] = df2['Timestamp'].diff()

        df = pd.concat([df1, df2], ignore_index=True)

    df = df.sort_values(by=['Timestamp']).reset_index(drop=True)
    df['IMD'] = df['Timestamp'].diff()
    df = df.drop(columns=['Contents', 'Attachments']).dropna()
    
    return df
    

if __name__ == '__main__':
    df = read_json_files()
    
    # Convert time deltas to seconds
    df['Time_Delta_Seconds'] = df['IMD'].dt.total_seconds()  

    # Drop NaN (first row has NaN because there's no previous timestamp)
    df_to_plot = df.query("Time_Delta_Seconds <= 3600")
    
    time_deltas = df_to_plot['Time_Delta_Seconds'].dropna()

    # lambda_param = len(time_deltas.to_list()) / sum(time_deltas.to_list())
    lambda_param = np.log(2) / time_deltas.median()
    print(f"lambda param = {lambda_param}")
    print(f"Rate parameter = {1/lambda_param}")
    print(f"Estimated median {(np.log(2) / lambda_param)}")
    print(f"Sample median {time_deltas.median()}")
    print(f'Sample size {time_deltas.count()}')
    mu = 1 / lambda_param
    b = 1 / (lambda_param * lambda_param)  


    # Plot Histogram
    # plt.figure(figsize=(6,4))
    plt.hist(time_deltas, bins=100, edgecolor='blue', alpha=0.7, density=True,)
    x = np.linspace(min(time_deltas), max(time_deltas), 100)
    pdf = lambda_param * np.exp(-lambda_param * x)
    # cdf = 1 - np.exp(-lambda_param * x)
    # positive_half_laplace = (1 / 2 * b) * np.exp(- (abs(x - mu) / b))

    plt.plot(x, pdf, 'r', linewidth=2)
    # plt.plot(x, cdf, 'g', linewidth=2)
    # plt.plot(x, positive_half_laplace, 'b', linewidth=2)

    # Add mean and median text to the plot
    # plt.text(lambda_param, 0.01, f'lamda: {lambda_param:.2f}', color='blue', ha='center', fontsize=12)
    # plt.text(time_deltas.median(), 0.01, f'Median: {time_deltas.mean():.2f}', color='green', ha='center', fontsize=12)



    
    plt.xlabel('Inter-Message Delay (Seconds)')
    plt.ylabel('Frequency')
    plt.title('Histogram of Inter-Message Delay (Seconds)')
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show Plot
    plt.savefig("plots/discord_imd_plot.png", format="png", dpi=1000, bbox_inches="tight")
    # plt.show()

    

    



