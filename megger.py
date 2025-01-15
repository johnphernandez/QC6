#########################################################################################################################
# This Script is Meant to be Run to see if there was a Megger Test Done on that Specfifc Module (Makes new Spreadsheet) #
#########################################################################################################################

import os
import sys
import tomli
from termcolor import colored
from datetime import datetime
import argparse
from checkconnections import load_toml, connect


def format(data):
    
    dt = datetime.now()
    str_date = dt.strftime("%Y-%m-%d_%H-%M")
    
    os.makedirs("Results", exist_ok = True)
    os.chdir("Results")
    
    os.makedirs(data["CAEN_INFO"]["Name"],exist_ok = True)
    os.chdir(data["CAEN_INFO"]["Name"])
    
    os.makedirs("Megger_Test",exist_ok = True)
    os.chdir("Megger_Test")
    
    os.chdir("../../..")
    os.popen("pwd")
    os.popen('cp megger_template.xlsx ./Results/'+data["CAEN_INFO"]["Name"]+'/Megger_Test/Megger_Test_'+str_date+'.xlsx')




if __name__ == '__main__':
    parser = argparse.ArgumentParser(description = "Script to Copy Megger Test Spreadsheet for New Test")
    parser.add_argument("-c", "--config", action = "store", dest = "config", help = "config = Name of config file")
    args = parser.parse_args()

    data: dict = load_toml(args.config)
    format(data)
    
    print(colored("New Megger Test Spreadsheet Created","green"))
