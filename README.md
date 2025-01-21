# QC6

This repository contains python scripts for performing QC6 tests on GEM detectors using CAEN SYX527 power supplies. 
NOTE : These scripts are intended to work on a Linux based OS.

```
QC6
├── README.md
├── checkconnections.py		: Check connection between PC and CAEN
├── megger.py				: Copy Excel sheet for the Megger Test
├── megger_template.xlsx	: Template for Megger Test
├── stresstest.py			: Applies voltage in steps, one channel at a time
├── iv+sstest.py			: Performs an IV Scan during ramp up, then does a short stability test
├── longstabilitytest.py	: Monitor trips over a long period of time
├── Config
│   └── Example.toml		: Example Config file for these tests
└── Plotting
	├── stresstestplot.py	: Plots the resolts of the Stress test
	├── ivplot.py			: Plots Current vs. Voltage for every channel
	└── stabilityplot.py	: Plots trips over time for either stability test
```

## Required Software

Two main libraries are needed to use these python scripts:
 - CAENHVWrapper : Software library for all CAEN Power supplies, available for C/C++ and LabView Environments
	- https://www.caen.it/products/caen-hv-wrapper-library/

 - pycaenhv : Provides access to all CAENHVWrapper functionality in pure python with no complilation needed. This needs to be added to the python path of the PC running these scripts
 	- https://github.com/vasoto/pycaenhv

## Desription of Each Script

Use -h for help with any of the scripts

`checkconnection.py` : Checks for a connection between the CAEN and PC based on information in the config file

`megger.py` : Copies the `megger_template.xlsx` file into `Results/Detector_Name/Megger_Test`, where `Detector_Name` is the name of the detector given in the config file

`stresstest.py` : Ramps up the voltage in steps one channel at a time until the max number of trips is reached or the max voltage is held for one minute

`iv+sstest.py` : Records Current and Voltage on all channels during ramp up, then monitors the trips while holding th e voltages for two hours

`longstabilitytest.py` : Ramps up the voltages and then holds them for 15 hours while monitoring the number of trips

## Future Work

These scripts are designed to be generalized for use with other detectors and CAEN systems. Currently tests have been done using a GE2/1 M6 and M7 module with a SY5527, but further support is being working on.
