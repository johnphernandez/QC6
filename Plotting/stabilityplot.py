import matplotlib.pyplot as plt
import mplhep as hep
import pathlib
import os
import numpy as np
from pprint import pprint
import argparse
import sys
from datetime import datetime

hep.style.use("ROOT")

def plot(file, long):

    f = open(file)
    df = f.read()
    if df == "":
        print("No Data in file")
        sys.exit()
        
    
    path = pathlib.Path(file)
    
    results = str(path.parent) + "/Plots"
    
    os.makedirs(results, exist_ok = True)
    
    detector_name = results.split("/")[1]
    
    time = [0]
    trips = [0]
    timestart = 0
    totaltrips = 0
    
    split = df.split("\n")
    
    for line in split:
        if "Started" in line:
            line = line.replace("Started at ","")
            timestart = datetime.strptime(line,"%Y-%m-%d_%H-%M")
        elif "Channels" not in line and "at" not in line and line != "":
            l = line.split(",")
            currenttime = datetime.strptime(l[-1],"%Y-%m-%d_%H-%M")
            timeelapsed = (currenttime.day - timestart.day)*24 + (currenttime.hour - timestart.hour) + (currenttime.minute - timestart.minute) / 60
            time.append(timeelapsed)
            trips.append(totaltrips)
            totaltrips += 1
            time.append(timeelapsed)
            trips.append(totaltrips)
        elif "Test" in line:
            line = line.replace("Test finished at ","")
            currenttime = datetime.strptime(line,"%Y-%m-%d_%H-%M")
            timeelapsed = (currenttime.day - timestart.day)*24 + (currenttime.hour - timestart.hour) + (currenttime.minute - timestart.minute) / 60
            time.append(timeelapsed)
            trips.append(totaltrips)
            
    fig, ax = plt.subplots(figsize=(11, 8), constrained_layout=False)
    
    ax.plot(time,trips,marker = "o")
    ax.set_xlabel("Time [h]")
    ax.set_ylabel("Trips")
    if long:
        ax.set_title(detector_name + " Long Stability Test")
    else:
        ax.set_title(detector_name + " Short Stability Test")
    fig.savefig(results + "/" + path.stem + ".png")
    
            
            
            

if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description = "Script to plot ss Test")
    parser.add_argument("-f", "--file", action = "store", dest = "file", help = "file = File to be plotted")
    parser.add_argument("-l", "--long", action = "store_true", dest = "long", default = False, help = "Long = Flag to change title to 'Long Stability Test'")
    #parser.add_argument("-t", "--tgem", action = "store", dest = "tgem", default = True, help = "Prints channel names with triple gem"
    args = parser.parse_args()
    
                    
    if args.file == None:
        print("Need file name")
        sys.exit()
    plot(args.file, args.long)
