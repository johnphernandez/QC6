#####################################################################################################################################
# This Python Script is intended to run QC6's Long Stability Test on whatever detector / module you are working with / connected to #
#####################################################################################################################################
import os
import sys
import tomli #Import Library to read TOML file
import argparse
import math
import numpy as np
from time import sleep,time
from termcolor import colored
from datetime import datetime
from pprint import pprint
from pycaenhv.wrappers import init_system, deinit_system, get_board_parameters, get_channel_parameters, get_channel_parameter, set_channel_parameter, exec_command, get_crate_map
from pycaenhv.enums import CAENHV_SYSTEM_TYPE, LinkType
from checkconnections import connect, load_toml, shutdown #load_toml imports CAEN Information and creates a handle using a TOML Configuration File
from stresstest import pwroff



# Establish Global varibles
trips = 0

# Write Path to store results
def format(data):
    
    dt = datetime.now()
    str_date = dt.strftime("%Y-%m-%d_%H-%M")
    
    os.makedirs("Results", exist_ok = True)
    os.chdir("Results")
    
    os.makedirs(data["CAEN_INFO"]["Name"],exist_ok = True)
    os.chdir(data["CAEN_INFO"]["Name"])
    
    os.makedirs("LS_test",exist_ok = True)
    os.chdir("LS_test")
    
    os.chdir("../../..")
    
    path = "Results/" + data["CAEN_INFO"]["Name"] + "/LS_test/LStest_" + str_date + ".txt"
    file = open(path, "a")
    file.write("Started at " + str_date + "\n")
    file.write("Channels, Timestamp\n")
    file.close
    
    return path

def checktrips(handle,data,Voltages,path,tripmax,step):
    global trips
    string2 = ""
    for row in Voltages:
        if get_channel_parameter(handle,data["CAEN_INFO"]["Slot"], row[0],"Pw") == 0 and row[step] != 0:
            string2 += str(row[0]) + ","
    if string2 == "":
        return True
    else:
        trips += 1
        dt = datetime.now()
        str_date = dt.strftime("%Y-%m-%d_%H-%M")
        string2 += str_date
        with open(path, "a") as file:
            file.write(string2 + "\n")
            file.close()
        print("Trip on Channels:" + string2)
        exec_command(handle,"ClearAlarm")
        if trips <= tripmax:
            print("Waiting 60 seconds")
            sleep(60)
            for row in Voltages:
                if row[step] != 0:
                    set_channel_parameter(handle,data["CAEN_INFO"]["Slot"], row[0],"Pw",1)
                    sleep(0.2)
            rup = 1 
            while rup == 1:
                rup = 0
                for row in Voltages:
                    if get_channel_parameter(handle,data["CAEN_INFO"]["Slot"], row[0],"Status") == "rup":
                        rup = 1
                    temp = checktrips(handle,data,Voltages,path,tripmax,step)
                    sleep(0.1)
        else:
            return False
        print("\nResuming Test\n")
        return False
        
    


def longstable(handle,data,vstart,vstep,vmax,itrip,tripmax,stabletime,endholdtime,endfoilvoltage):
    global trips
    Voltages = []
    channels = []
    resistances = [1.125, 0.560, 0.438, 0.550, 0.875, 0.525, 0.625] # Equivalent Resistance in Mega Ohms 
    if data["Detector_Info"]["isTGEM"] == True: # This Area of the code takes in information from the Configuration file
        if data["Detector_Info"]["Layer"] == 1:
            channels = [6, 5, 4, 3, 2, 1, 0]
        elif data["Detector_Info"]["Layer"] == 2:
            channels = [13, 12, 11, 10, 9, 8, 7]
        else: 
            print(colored("Layer must be 1 or 2", "yellow"),end = "")
            shutdown(handle)
        # Section Creates a Table of Voltages for Each Channel according to the resistances given    
        for chan in channels:
            Voltages.append([chan])
        for v in range (vstart,vmax,vstep):
            Ieq = v / (4.698) 
            for i in range(7):
                Volt = Ieq*resistances[i]
                if Volt >= get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],Voltages[i][0], "SVMax"):
                    Volt = get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],Voltages[i][0], "SVMax")
                Voltages[i].append(Volt)
        Ieq = vmax / 4.698
        for i in range(7):
            Volt = Ieq*resistances[i]
            if Volt >= get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],Voltages[i][0], "SVMax"):
                Volt = get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],Voltages[i][0], "SVMax")
            Voltages[i].append(Volt)
        for i in range(7):
            if Voltages[i][0] in [5,3,1,12,10,8]:
                Voltages[i].append(endfoilvoltage)
            else:
                Voltages[i].append(0)
    
        
    path = format(data)
        
    for row in Voltages:
        set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"Pw",1)
        sleep(0.1)
    
    # Set Voltage to first value in list
    step = 1
    while step < len(Voltages[0])-1 and trips <= tripmax:
        vchamber = 0
        for row in Voltages:
            set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"V0Set", row[step])
            sleep(0.1)
            vchamber += row[step]
        print("Setting Voltage to %f" % (vchamber))
        # Cycling through the rest of the voltage values and recording at each stepp
        rup = 1 
        while rup == 1 and trips <= tripmax:
            rup = 0
            for row in Voltages:
                if get_channel_parameter(handle,data["CAEN_INFO"]["Slot"], row[0],"Status") == "rup":
                    rup = 1
                temp = checktrips(handle,data,Voltages,path,tripmax,step)
                if trips >= tripmax:
                    return False
                sleep(0.1)

        start = time()
        while int(time() - start) < stabletime and trips <= tripmax:
            for row in Voltages:
                if checktrips(handle,data,Voltages,path,tripmax,step) == False:
                    start = time()    
                    if trips >= tripmax:
                        return False
                sleep(0.1)                     
        step += 1
        
    # Start of LS Test
    for row in Voltages:
        set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"V0Set",row[step])
        sleep(0.1)
        if row[step] == 0:
            set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"Pw",0)
    print("Starting Long Stabilty Test")
    start = time()
    while int(time() - start) < endholdtime*3600 and trips <= tripmax:
        for row in Voltages:
            if checktrips(handle,data,Voltages,path,tripmax,step) == False:
                if trips >= tripmax:
                    return False
                sleep(0.1)
            
    # Powering off all channels
    for row in Voltages:
        set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"Pw",0)
    dt = datetime.now()
    str_date = dt.strftime("%Y-%m-%d_%H-%M")
    file = open(path,"a")
    file.write("Test finished at" + str_date)
    file.close()

    
if __name__ == '__main__':
    #Parsing Arguments
    parser = argparse.ArgumentParser(description = "Script to Run the LS Test")
    parser.add_argument("-c", "--config", action = "store", dest = "config", help = "config = Name of config file")
    parser.add_argument("-s", "--vstart", action = "store", dest = "vstart", default = 200, help = "Starting voltage value across all of the dividers, default is 200V")
    parser.add_argument("-m", "--vmax" , action = "store", dest = "vmax" , default = 4200, help = "Max voltage value across all channels, default is 4200V")
    parser.add_argument("-t", "--vstep", action = "store", dest = "vstep" , default = 200, help = "Voltage step size, default is 200V")
    parser.add_argument("-b", "--stabletime", action = "store", dest = "stabletime", default = 10, help = "stabilizationtime = time to hold at each step prior to recording, default value is 10 seconds")
    parser.add_argument("-i", "--itrip", action = "store", dest = "itrip", default = 2, help = "itrip = max current allowed before it's considered a trip, default is 2uA")
    parser.add_argument("-x", "--tripmax", action = "store", dest = "tripmax", default = 200, help = "tripmax = maximum number of trips allowed for LStest, default is 200 before the test stops")
    parser.add_argument("-e", "--endholdtime", action = "store", dest = "endholdtime", default = 15, help = "endholdtime = hold time after reaching the max voltage on the foil, default value is fifteen hours")
    parser.add_argument("-f", "--endfoilvoltage", action = "store", dest = "endfoilvoltage", default = 580, help = "endfoilvoltage = voltage to be put across top foils during ss test, default is 550V")
    args = parser.parse_args()
    
    data,handle = connect(args.config)
    
    
    try:
        Status = longstable(handle,data, int(args.vstart), int(args.vstep), int(args.vmax),int(args.itrip),int(args.tripmax),float(args.stabletime),float(args.endholdtime),float(args.endfoilvoltage))
        if Status == False:
            print(colored("Test Failed: Max number of trips exceeded","red"))
            pwroff(data,handle)
        else:
            print(colored("Test is Finished","green"))
    except KeyboardInterrupt:
        print(colored("KeyboardInterrupt Encountered","red"))
        print()
        if args.off == "": 
            print(colored("Power off all channels?","yellow"))
            args.off = input()
        if args.off in ['y','Y','yes',"Yes"]:
            print(colored("Powering off all channels","yellow"))
            pwroff(data,handle)
        else:
            print(colored("Channels may still be powered on, check before working on any hardware!","yellow"))

        
    shutdown(handle)
