#########################################################################################################################
# This Script is Meant to Run and Stores the Results of QC6's 'Stress Test', on whatever detector / Module you are using#
#########################################################################################################################

#Import Necessary Items
import os
import sys
import tomli #Import Library to read TOML file
import argparse
from termcolor import colored
from datetime import datetime
from pycaenhv.wrappers import init_system, deinit_system, get_board_parameters, get_channel_parameters, get_channel_parameter, set_channel_parameter, exec_command, get_crate_map
from pycaenhv.enums import CAENHV_SYSTEM_TYPE, LinkType
from time import sleep,time
import math 
from checkconnections import connect, load_toml, shutdown #load_toml imports CAEN Information and creates a handle using a TOML Configuration File
import numpy as np


#Global Variables - (Variables that are called in more than one Function)
trip_count = 0
i = 0

def pwroff(data,handle):
    if data["CAEN_INFO"]["System_Type"] in ["SY5527","SY4527"]:
        if data["Detector_Info"]["Layer"] == 1:
            chans = [6,5,4,3,2,1,0]
        elif data["Detector_Info"]["Layer"] == 2:
            chans = [13,12,11,10,9,8,7]
        else:
            print("Unknown Layer Number, powering off all channels")
            chans = list(range(get_crate_map(handle)["channels"][data["CAEN_INFO"]["Slot"]]))
    else:
        chans = list(range(get_crate_map(handle)["channels"][data["CAEN_INFO"]["Slot"]]))    #This needs to be tested with other CAEN power supplies

    for c in chans:
        set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],c, "Pw", 0)
        sleep(0.1)


#Creates Result & 'Stress Test' Directories and writes results to a text file
def format(data):
        
    dt = datetime.now()
    str_date = dt.strftime("%Y-%m-%d_%H-%M")
    
    os.makedirs("Results", exist_ok = True)
    os.chdir("Results")
    
    os.makedirs(data["CAEN_INFO"]["Name"],exist_ok = True)
    os.chdir(data["CAEN_INFO"]["Name"])
    
    os.makedirs("Stress_Test",exist_ok = True)
    os.chdir("Stress_Test")

    os.chdir("../../..")
    
    path = "Results/" + data["CAEN_INFO"]["Name"] + "/Stress_Test/stress_" + str_date + ".txt"
    file = open(path,"w")
    file.write("Time , Channel, Voltage of Trip\n")
    file.close()
    return path

    
# Checking Trips Function, to be called when at each foil
def check_trips(handle,slot,channel,path,tripmax):
    
    if get_channel_parameter(handle,slot,channel,"Pw") == 0:
        global trip_count
        trip_count += 1
        global i 
        
        if trip_count > tripmax: #If the trip count reaches the max number of trips allowed we must reduce the voltage
            exec_command(handle,"ClearAlarm")
            return
        i -= 21      # This equates to dropping 200V when testing TGEM detectors in QC6
        if i < 1:
            i = 1 #Can't have a negative voltage, if voltage reduced below zero we set i = 1

        dt = datetime.now()
        str_time = dt.strftime("%Y-%m-%d_%H-%M-%S")
        trip_voltage = get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],channel, "VMon")
        with open(path,"a") as file: #Records trip to a text file
            file.write("%s,%i,%s\n" % (str_time,channel,str(round(trip_voltage,2))))
            print("Trip occured at %s, on channel %i at %s V" % (str_time,channel,str(round(trip_voltage,2))))
        exec_command(handle,"ClearAlarm")
        print("Waiting for Fifteen Seconds\n") #We wait a longer amount of time here to give voltage time to ramp down
        sleep(15)
        if trip_count == tripmax:
            return
        set_channel_parameter(handle,slot,channel, "Pw", 1) #Turns Channel Back on after trip
        sleep(1)
    else:
        sleep(0.1)
                
#Function to Run Stress Test
def stress(handle,data,vstart,vstep,vmax,gskip,itrip,holdtime,endholdtime,tripmax):
    Voltages = []
    channels = []
    if data["Detector_Info"]["isTGEM"] == True: # This Area of the code takes in information from the Configuration file
        if data["Detector_Info"]["Layer"] == 1:
            channels = [5, 3, 1]
        elif data["Detector_Info"]["Layer"] == 2:
            channels = [12, 10, 8]
        else: 
            print(colored("Layer must be 1 or 2", "yellow"),end = "")
            shutdown(handle)
        for skip in sorted(gskip, reverse = True):
            del channels[skip-1]
        for chan in channels:
            temp = []
            temp.append(chan)
            for v in range(vstart,vmax, vstep):
                temp.append(v)
            temp.append(vmax)    
            Voltages.append(temp)
            
    path = format(data)
    for row in Voltages:
        set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"I0Set",itrip) #Set current limit
        sleep(0.1)
        global i
        global trip_count
        trip_count = 0
        i = 1
        set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"Pw",1)
        sleep(0.1)
        print("Starting Channel %i\n" % (row[0]))
        
        while (i < len(row)): #Add Check for max number of trip
            if row[i] > get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "SVMax"):
                set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "V0Set", get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "SVMax"))
                sleep(0.1)
                i = len(row) - 1
                row[i] = get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "SVMax")
                
            else:
                set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "V0Set",row[i])
                sleep(0.1)
                    
            while abs(row[i] - get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0],"VMon")) > 1 and get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "Pw") == 1:
                check_trips(handle,data["CAEN_INFO"]["Slot"],row[0],path,tripmax)
            start = time()
            
            if trip_count >= tripmax:
                break
                
            elif i == len(row) - 1:
                print("Holding for 60 seconds\n")
                while int(time() - start) < endholdtime and get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "Pw") == 1:
                    #print("Holding for 60 seconds\n")
                    check_trips(handle,data["CAEN_INFO"]["Slot"],row[0],path,tripmax)
            else:
                while int(time() - start) < holdtime and get_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "Pw") == 1:
                    check_trips(handle,data["CAEN_INFO"]["Slot"],row[0],path,tripmax)
                    
            check_trips(handle,data["CAEN_INFO"]["Slot"],row[0],path,tripmax)
            i += 1
        #End of test for this channel
        set_channel_parameter(handle,data["CAEN_INFO"]["Slot"],row[0], "Pw",0)
                


if __name__ == '__main__':
    #Parsing Arguments
    parser = argparse.ArgumentParser(description = "Script to Run the Stress Test")
    parser.add_argument("-c", "--config", action = "store", dest = "config", help = "config = Name of config file")
    parser.add_argument("-s", "--vstart", action = "store", dest = "vstart", default = 0, help = "Starting voltage value, default is 0V")
    parser.add_argument("-m", "--vmax" , action = "store", dest = "vmax" , default = 650, help = "Max voltage value, default is 650V")
    parser.add_argument("-t", "--vstep", action = "store", dest = "vstep" , default = 10, help = "Voltage step size, default is 10V")
    parser.add_argument("-g", "--gskip", action = "store", nargs = "+",dest = "gskip", default = [], help = "GEM foil to be skipped")
    parser.add_argument("-i", "--itrip", action = "store", dest = "itrip", default = 2, help = "itrip = max current allowed before it's considered a trip, default is 2uA")
    parser.add_argument("-x", "--tripmax", action = "store", dest = "tripmax", default = 5, help = "tripmax = maximum number of trips allowed, default is 5 before the test stops")
    parser.add_argument("-l", "--holdtime", action = "store", dest = "holdtime", default = 5, help = "hold time = time to hold at each step, default value is 5 seconds")
    parser.add_argument("-e", "--endholdtime", action = "store", dest = "endholdtime", default = 60, help = "endholdtime = hold time after reaching the max voltage on the foil, default value is 60 seconds")
    parser.add_argument("-o", "--off", action="store", dest = "off", default="", help = "off = Power off all channels during a keyboard interrupt if 'yes'")
    args = parser.parse_args()
    
    data,handle = connect(args.config)
    gskip = []
    for skip in args.gskip:
        g_int = int(skip)
        if g_int not in range(0,4):
            print(colored("Only Allowed Values 1,2,3", "red"),end = "")
            shutdown(handle)
        gskip.append(g_int)
        
    try:
        stress(handle,data,int(args.vstart), int(args.vstep),int(args.vmax), gskip, int(args.itrip),int(args.holdtime),int(args.endholdtime),int(args.tripmax))
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
        
