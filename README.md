# multilog

Masurement data recording and visualization using various devices. This is still under development.

## <u>About Us</u>
The project is being processed by the model experiments group at the IKZ - Leibniz Institut für Kristallzüchtung.

## <u>Programs</u>
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

## <u> Operation </u>

Start the main sample.py in a command window:
python sample.py

The flag --h shows some command line parameters

## Referencing

If you use this code in your research please cite:

A. Enders-Seidlitz, J. Pal, and K. Dadzis 2022 Model experiments for Czochralski crystal growth processes using inductive and resistive heating. *IOP Conf. Ser.* **EPM 2021** (in press)

## Acknowledgements

[This project](https://www.researchgate.net/project/NEMOCRYS-Next-Generation-Multiphysical-Models-for-Crystal-Growth-Processes) has received funding from the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation programme (grant agreement No 851768).

<img src="https://raw.githubusercontent.com/nemocrys/pyelmer/master/EU-ERC.png">
