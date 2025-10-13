import pandas as pd
import matplotlib.pyplot as plt
import os

# INPUT
measDirs = ["../measdata_2025-10-13_#17",
            "../measdata_2025-10-13_#18"
            ]
measFile = "DAQ-6510.csv"

# channel names in measfile
device_channels = ['Pt-100_5 air',
                #    'battery'
                   ]

time_mode = "rel" # absolute "abs" or relative "rel" time

# LOAD
dfs = {} # store dataframes in dictionary
for dir in measDirs:
    dfs[dir] = pd.read_csv(os.path.join(dir,measFile), skiprows=1) 
    # Convert time_abs to datetime
    dfs[dir]['time_abs'] = pd.to_datetime(dfs[dir]['time_abs'])

print(dfs)

# PLOT
plt.subplots(figsize=(8,4))

for dir in measDirs:
    df = dfs[dir]
    for ch in device_channels:
        if time_mode == 'abs':
            plt.plot(df['time_abs'], df[ch],label=f"{dir} {ch}")
        else:
            plt.plot(df['time_rel'], df[ch],label=f"{dir} {ch}")


plt.xlabel("Time")
plt.ylabel("Temperature [°C]")
plt.legend(bbox_to_anchor=(1.05, 1.0), loc='upper left')
plt.grid(linestyle=":")
plt.tight_layout()
plt.savefig("cmpTemperatures.png")
plt.show()