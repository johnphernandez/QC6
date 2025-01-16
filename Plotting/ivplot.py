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

def ivscan(file, gem):
    df =  df = read_csv(file, delimiter=",")

    gems = {6:"Drift",5:"G1T",4:"G1B",3:"G2T",2:"G2B",1:"G3T",0:"G3B"}

    if df.empty:
        print("No data in " + str(file) + ", skipping...")
        return 0
    
    path = pathlib.Path(file)
    
    results = str(path.parent) + "/Plots"
    
    os.makedirs(results, exist_ok = True)
    
    detector_name = results.split("/")[1]
    
    chan = []
    for key in df:
        string = key[2:]
        string = string[:-7]
        if string not in chan:
            chan.append(string)
    
    fig, ax = plt.subplots(figsize=(11, 8), constrained_layout=False)

    if gem:
        for c in chan:
            if int(c) > 6:
                c = int(c)-7
            ax.plot(df["CH" + c + "Voltage"],df["CH" + c + "Current"],marker = "o",label = gems[int(c)])
    else:
        for c in chan:
            ax.plot(df["CH" + c + "Voltage"],df["CH" + c + "Current"],marker = "o",label = "Channel %s" % c)
    
    ax.set_xlabel("Voltage [V]")
    ax.set_ylabel("Current [$\mu$A]")
    ax.set_title(detector_name + " IV Scan")
    ax.legend(frameon = True, loc = "upper right", fontsize = 12)
    fig.savefig(results + "/" + path.stem + ".png")
        

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = "Script to Run the LS Test")
    parser.add_argument("-f", "--file", action = "store", dest = "file", help = "file = File to be plotted")
    parser.add_argument("-g", "--gem", action = "store", dest = "gem", default = True, help = "Converts to gem terminology, Channel 6 -> Drift")    
    args = parser.parse_args()
    
    if args.file == None:
        print("Need file name")
        sys.exit()
    ivscan(args.file, args.gem)
        
