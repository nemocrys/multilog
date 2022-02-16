# multilog

Masurement data recording and visualization using various devices.

The project is developed and maintained by the [**Model experiments group**](https://www.ikz-berlin.de/en/research/materials-science/section-fundamental-description#c486) at the Leibniz Institute for Crystal Growth (IKZ).

### Referencing
If you use this code in your research, please cite our article (available with open access):

> A. Enders-Seidlitz, J. Pal, and K. Dadzis, Model experiments for Czochralski crystal growth processes using inductive and resistive heating *IOP Conference Series: Materials Science and Engineering*, 1223 (2022) 012003. https://doi.org/10.1088/1757-899X/1223/1/012003.

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

## Acknowledgements

[This project](https://www.researchgate.net/project/NEMOCRYS-Next-Generation-Multiphysical-Models-for-Crystal-Growth-Processes) has received funding from the European Research Council (ERC) under the European Union's Horizon 2020 research and innovation programme (grant agreement No 851768).

<img src="https://raw.githubusercontent.com/nemocrys/pyelmer/master/EU-ERC.png">
