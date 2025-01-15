######################################################################################
# This Code is Meant to Check your Connection to the CAEN and Initializes the System # 
######################################################################################

import sys
from pycaenhv.wrappers import init_system, deinit_system
from pycaenhv.enums import CAENHV_SYSTEM_TYPE, LinkType
import tomli 
from termcolor import colored 
import argparse


def load_toml(config) -> dict: 
    """Load TOML data from File"""
    
    with open(config, 'rb') as f:
        toml_data: dict = tomli.load(f)
        return toml_data

def shutdown(handle):
    print("Deinitializing System")
    deinit_system(handle)
    print("Bye-Bye")
    sys.exit()

def connect(config):    
    if config is None:
        print(colored("Please Enter Config File","yellow"))
        sys.exit()
 #LOAD TOML AS DICT
    data: dict = load_toml(config)
 # Check the System Name
    try:
        system_type = CAENHV_SYSTEM_TYPE[data["CAEN_INFO"]["System_Type"]]
    except:
        print(colored("Issue with System Type","red"))
        sys.exit()
 # Checking Link Type        
    try:
        link_type = LinkType[data["Link"]["link_type1"]]
    except:
        print(colored("Issue with Link Type","red"))
        sys.exit()
 # Check Board Connection
    try:
        handle = init_system(system_type, link_type, data["Link"]["IP_Address"], data["Link"]["username"],data["Link"]["password"])
    except: 
        print(colored("Issue with creating handle, Check IP Address, username, or password", "red"))
        sys.exit()
    return data,handle
        


if __name__ == '__main__':
    # PARSING ARGS
    parser = argparse.ArgumentParser(description = "Checks Your Connection to the CAEN")
    parser.add_argument("-c", "--config", action = "store", dest = "config", help = "config = Name of config file")
    
    args = parser.parse_args()
    data,handle = connect(args.config)    

    print(colored("connection is good", "green"))
    shutdown(handle)
        
    
    
