# multilog

Masurement data recording and visualization using various devices. This is still under development.

## About Us
The project is being processed by the **Model experiments** group at the Leibniz Institute for Crystal Growth (IKZ).
[Group on IKZ homepage](https://www.ikz-berlin.de/en/research/materials-science/section-fundamental-description)


## Programs
Python 3 is used.

Script	    		|	 Related Device  
--------------------|------------------------
Pyrometer.py        |    Impac IGA 6/23 and IGAR 6 Adv.
Pyrometer_Array.py  |    Impac Series 600  
DAQ_6510.py         |    Multimeter 
Arduino.py          |    Not yet fully implemented

__Other files__ 
1. sample.py
    * The main script to start
2. config.ini 
    * configuration file for the used devices

__Further modules to be integrated here__

[IR Camera](https://github.com/nemocrys/IRCamera)

## Operation

Start the main sample.py in a command window:
python sample.py

The flag --h shows some command line parameters

## Referencing

If you use this code in your research, please cite our article:

A. Enders-Seidlitz, J. Pal, and K. Dadzis, Model experiments for Czochralski crystal growth processes using inductive and resistive heating. *IOP Conference Series: Materials Science and Engineering, Electromagnetic Processing of Materials (EPM 2021)*, 2022, In press.

## Acknowledgements

[This project](https://www.researchgate.net/project/NEMOCRYS-Next-Generation-Multiphysical-Models-for-Crystal-Growth-Processes) has received funding from the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation programme (grant agreement No 851768).

<img src="https://raw.githubusercontent.com/nemocrys/pyelmer/master/EU-ERC.png">
