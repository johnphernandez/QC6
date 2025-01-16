import matplotlib.pyplot as plt
from pandas import read_csv
import mplhep as hep
import pathlib
import os
import numpy as np
from pprint import pprint
import argparse
import sys

hep.style.use("ROOT")

def stress(file, gem):

    gems = {5:"GEM 1",3:"GEM 2",1:"GEM 3"}
    
    df =  df = read_csv(file, delimiter=",", names=["date", "Chan", "V"],skiprows = 1)

    if df.empty:
        print("No data in " + str(file) + ", skipping...")
        return 0
    
    path = pathlib.Path(file)
    
    results = str(path.parent) + "/Plots"
    
    os.makedirs(results, exist_ok = True)
    
    detector_name = results.split("/")[1]
    
    data = {}
    chan = []
    for channel in df["Chan"]:
        if channel not in chan:
            chan.append(channel)
            data[channel] = {}
    for c in chan:
        data[c]["trip"] = []
        data[c]["volt"] = []
    j = 0
    for i in range(len(df["V"])):
        data[df["Chan"][i]]["volt"].append(float(df["V"][i]))
        try:
            data[df["Chan"][i]]["trip"].append(data[df["Chan"][i]]["trip"][-1] + 1)
        except:
            data[df["Chan"][i]]["trip"].append(1)
    
    fig, ax = plt.subplots(figsize=(10, 8), constrained_layout=False)
    
    if gem:
        for c in chan:
            if c > 6:
                c = c-7
            ax.plot(data[c]["trip"], data[c]["volt"], marker = "o",label = gems[c])
    else:
        for c in chan:
            ax.plot(data[c]["trip"], data[c]["volt"], marker = "o",label = "Channel %s" % c)
    
        
    ax.set_xlabel("Trip Iteration")
    ax.set_ylabel("Voltage [V]")
    ax.set_title(detector_name + " Stress Test")
    ax.legend(frameon = True, loc = "upper right")
    
    fig.savefig(results + "/" + path.stem + ".png")
    

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = "Script to Run the LS Test")
    parser.add_argument("-f", "--file", action = "store", dest = "file", help = "file = File to be plotted")
    parser.add_argument("-g", "--gem", action = "store", dest = "gem", default = True, help = "Converts to gem terminology, Channel 6 -> Drift")
    args = parser.parse_args()
    
    if args.file == None:
        print("Need file name")
        sys.exit()
    stress(args.file, args.gem)
        

