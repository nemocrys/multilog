# coding=utf8


import argparse
import configparser
import DAQ_6510
import Pyrometer
import Pyrometer_Array
import Arduino
import sys
import os
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import numpy as np
import datetime
import time
import pyqtgraph as pg
from functools import partial
import random
import matplotlib


print ("Running sample.py ...")
parser = argparse.ArgumentParser()
parser.add_argument('-test', help='test mode without COM ports [optional, default=false]', action = 'store_true')
parser.add_argument('-time', help='test mode with timestamp from DAQ [optional, default=false]', action = 'store_true')
parser.add_argument('-cfg', help='config file name [optional, default="config.ini"]', default='config.ini')
parser.add_argument('-dt', help='sampling steps in miliseconds [optional, default=1000]', type=int, default=1000)
parser.add_argument('-nplc', help='overall NPLC for DAQ [optional]', type=float)
parser.add_argument('-lsync', help='overall line sync [optional, default=1]', type=int, default=1)
parser.add_argument('-ocom', help='overall offset compensation [optional, default=1]', type=int, default=1)
parser.add_argument('-azer', help='overall automatic zero compensation [optional, default=0]', type=int, default=0)
parser.add_argument('-adel', help='overall autodelay [optional, default=1]', type=int, default=1)
parser.add_argument('-debug_pyro', help='show the interface data [optional, default=false]', action = 'store_true')
parser.add_argument('-debug_array', help='show the interface data [optional, default=false]', action = 'store_true')
parser.add_argument('-debug_daq', help='show the interface data [optional, default=false]', action = 'store_true')
parser.add_argument('-debug_arduino', help='show the interface data [optional, default=false]', action = 'store_true')

args = parser.parse_args()
parser.print_help()


# some initialisations
print ('\n')
print ('Initialising...')
print ('===============')

if args.test:
    print ('Test mode...\n')
if args.time:
    print ('Timestamp mode from DAQ...\n')    
if args.debug_daq:
    print ('Debug mode for Keithley DAQ-6510...')
if args.debug_pyro:
    print ('Debug mode for Pyrometer...')
if args.debug_array:
    print ('Debug mode for Pyrometer array...')    
if args.debug_arduino:
    print ('Debug mode for Arduino...')    
    
    
DAQ_present = False
DAQ_lsync = bool(args.lsync)
DAQ_ocom = bool(args.ocom)
DAQ_azer = bool(args.azer)
DAQ_adel = bool(args.adel)
Pyro_present = False
Pyro_array_present = False
Arduino_present = False
Nb_Instruments = 0
Sampling_Timer = args.dt # in miliseconds



# read the config file
ConfigFileName = args.cfg
cp = configparser.ConfigParser()
print ('reading config file: '+ ConfigFileName + '\n')
cp.read(ConfigFileName)

ch_list = list(range(0)) # all channels, something from 101 ..120, 201..220, 501...., 601...
alias_list = list(range(0))
sensor_list = list(range(0)) # TE,TE,PT,DCV,TE,.....
factor_list = list(range(0))
offset_list = list(range(0))

daq_ch_list = list(range(0)) # only DAQ channels
daq_sensor_list = list(range(0))
daq_alias_list = list(range(0))
daq_range_list = list(range(0))
daq_nplc_list = list(range(0))
arduino_ch_list = list(range(0))
arduino_alias_list = list(range(0))
arduino_cmd_list = list(range(0))
arduino_read_id_list = list(range(0))
arduino_end_id_list = list(range(0))
arduino_position_list = list(range(0))
arduino_separator_list = list(range(0))
range_list = list(range(0)) # K,K,100,100mV,J,...

sensor_types = list(range(0))
sensor_unit_list = list(range(0)) #[°C], [mV]

pyro_model_list = list(range(0))
pyro_com_list = list(range(0))
pyro_alias_list = list(range(0))
pyro_tr_list = list(range(0))
pyro_em_list = list(range(0))
pyro_rate_list = list(range(0))
pyro_bits_list = list(range(0))
pyro_stop_list = list(range(0))
pyro_parity_list = list(range(0))
pyro_t90_list = list(range(0))
pyro_t90_times = list(range(0))
pyro_card_list = list(range(0))
pyro_distance_list = list(range(0))
pyro_array_model_list = list(range(0))
pyro_array_alias_list = list(range(0))
pyro_array_em_list = list(range(0))
pyro_array_t90_list = list(range(0))
pyro_array_t90_times = list(range(0))
pyro_array_card_list = list(range(0))
arduino_com_list = list(range(0))
arduino_rate_list = list(range(0))
arduino_bits_list = list(range(0))
arduino_stop_list = list(range(0))
arduino_parity_list = list(range(0))
instruments_list = list(range(0))
arduino_card_list = list(range(0))


for section_name in cp.sections():
    if section_name == 'Overflow':
        for name, value in cp.items(section_name):
            if name == 'daq-6510':
                daq_overflow = float(value.split(',')[0].replace(' ', ''))
            if name == 'pyro':
                pyro_overflow = float(value.split(',')[0].replace(' ', ''))
            if name == 'arduino':
                arduino_overflow = float(value.split(',')[0].replace(' ', ''))
    if section_name == 'PT-1000':
        for name, value in cp.items(section_name):
            if name == 'save':
                PT_1000_mode = value
                
    if section_name == 'Instruments': 
        for name, value in cp.items(section_name):
            if name == 'daq-6510':
                daq_onoff = value.split(',')[0].replace(' ', '')
                daq_com = value.split(',')[1].replace(' ', '')
                #daq_com = int(value.split(',')[1].replace(' ', ''))
                daq_rate = value.split(',')[2].replace(' ', '')
                daq_bits = value.split(',')[3].replace(' ', '')
                daq_stop = value.split(',')[4].replace(' ', '')
                daq_parity = value.split(',')[5].replace(' ', '')
                if daq_onoff == 'on':
                    DAQ_present = True
            if name == 'pyro':
                Nb_of_Pyrometer = int(value)
                pyro_card_list.append('Card-05')
                if Nb_of_Pyrometer != 0:
                    #for i in range(Nb_of_Pyrometer):
                        #pyro_card_list.append('Card-0' + str(5+i))
                    Pyro_present = True
                    Nb_Instruments += 1
                    instruments_list.append('Pyrometer')
            if name == 'pyro-array':
                pyro_array_onoff = value.split(',')[0].replace(' ', '')
                #pyro_array_onoff = int(value.split(',')[0].replace(' ', ''))
                pyro_array_com = int(value.split(',')[1].replace(' ', ''))
                pyro_array_rate = value.split(',')[2].replace(' ', '')
                pyro_array_bits = value.split(',')[3].replace(' ', '')
                pyro_array_stop = value.split(',')[4].replace(' ', '')
                pyro_array_parity = value.split(',')[5].replace(' ', '')
                pyro_array_card_list.append('Card-20')                
                if pyro_array_onoff == 'on':
                    Pyro_array_present = True
                    Nb_Instruments += 1
                    instruments_list.append('Pyro-array')   
                else:
                    Nb_of_pyro_array_heads = 0
            if name == 'arduino':
                Nb_of_Arduino = int(value)
                if Nb_of_Arduino != 0:
                    for i in range(Nb_of_Arduino):
                        arduino_card_list.append('Card-1' + str(i))
                    Arduino_present = True
                    Nb_Instruments += 1
                    instruments_list.append('Arduino')
    for name, value in cp.items(section_name):
        if DAQ_present:
            if section_name == 'Card-01':
                ch_list.append(name.replace('ch-', '1'))
                daq_ch_list.append(name.replace('ch-', '1'))
                daq_alias_list.append(value.split(',')[0])
                alias_list.append(value.split(',')[0])                
                sensor_list.append((value.split(',')[1]).replace(' ', ''))
                daq_sensor_list.append((value.split(',')[1]).replace(' ', ''))
                range_list.append((value.split(',')[2]).replace(' ', ''))
                daq_range_list.append((value.split(',')[2]).replace(' ', ''))
                daq_nplc_list.append((value.split(',')[3]).replace(' ', ''))
                factor_list.append((value.split(',')[4]).replace(' ', ''))
                offset_list.append((value.split(',')[5]).replace(' ', ''))
            if section_name == 'Card-02':
                ch_list.append(name.replace('ch-', '2')) 
                daq_ch_list.append(name.replace('ch-', '2'))
                daq_alias_list.append(value.split(',')[0])
                alias_list.append(value.split(',')[0])    
                val = value.split(',')[1].replace(' ', '')                
                sensor_list.append((value.split(',')[1]).replace(' ', ''))
                daq_sensor_list.append((value.split(',')[1]).replace(' ', ''))
                range_list.append((value.split(',')[2]).replace(' ', ''))
                daq_range_list.append((value.split(',')[2]).replace(' ', ''))
                daq_nplc_list.append((value.split(',')[3]).replace(' ', ''))
                factor_list.append((value.split(',')[4]).replace(' ', ''))
                offset_list.append((value.split(',')[5]).replace(' ', ''))
                
        if Pyro_array_present:
            if section_name == 'Card-20':
                ch_list.append(name.replace('ch-', '20'))
                pyro_array_alias_list.append(value.split(',')[0])
                alias_list.append(value.split(',')[0])
                pyro_array_em_list.append((value.split(',')[1]).replace(' ', ''))
                pyro_array_t90_list.append((value.split(',')[2]).replace(' ', ''))
                factor_list.append((value.split(',')[3]).replace(' ', ''))
                offset_list.append((value.split(',')[4]).replace(' ', ''))                
                times = value[value.find('('):].replace('(', '').replace(')', '')
                pyro_array_t90_times.append(times.split())
        
        if Pyro_present and section_name in pyro_card_list:
            if len(pyro_com_list) < Nb_of_Pyrometer:
                ch_list.append(name.replace('ch-', '5'))
                pyro_alias_list.append(value.split(',')[0])
                alias_list.append(value.split(',')[0])
                pyro_com_list.append((value.split(',')[1]).replace(' ', ''))
                pyro_tr_list.append((value.split(',')[2]).replace(' ', ''))
                pyro_em_list.append((value.split(',')[3]).replace(' ', ''))
                pyro_rate_list.append((value.split(',')[4]).replace(' ', ''))
                pyro_bits_list.append((value.split(',')[5]).replace(' ', ''))
                pyro_stop_list.append((value.split(',')[6]).replace(' ', ''))
                pyro_parity_list.append((value.split(',')[7]).replace(' ', ''))
                pyro_t90_list.append((value.split(',')[8]).replace(' ', ''))
                factor_list.append((value.split(',')[9]).replace(' ', ''))
                offset_list.append((value.split(',')[10]).replace(' ', ''))
                times = value[value.find('('):].replace('(', '').replace(')', '')
                pyro_t90_times.append(times.split())
                
        if Arduino_present and section_name in arduino_card_list:
            if name == 'com':
                arduino_com_list.append(value.split(',')[0])
                arduino_rate_list.append((value.split(',')[1]).replace(' ', ''))
                arduino_bits_list.append((value.split(',')[2]).replace(' ', ''))
                arduino_stop_list.append((value.split(',')[3]).replace(' ', ''))
                arduino_parity_list.append((value.split(',')[4]).replace(' ', ''))
            else:
                ch_list.append(name.replace('ch-', section_name[5:]))
                arduino_ch_list.append(name.replace('ch-', section_name[5:]))
                arduino_alias_list.append(value.split(',')[0])
                alias_list.append(value.split(',')[0])
                arduino_cmd_list.append((value.split(',')[1]).replace(' ', ''))
                arduino_read_id_list.append((value.split(',')[2]).replace(' ', ''))
                arduino_end_id_list.append((value.split(',')[3]).replace(' ', ''))
                arduino_position_list.append((value.split(',')[4]).replace(' ', ''))
                arduino_separator_list.append((value.split(',')[5]).strip(' ').replace('"', ''))
                factor_list.append((value.split(',')[6]).replace(' ', ''))
                offset_list.append((value.split(',')[7]).replace(' ', ''))
                

Nb_all_sensors = len(ch_list)
sensor_unit_list = ['°C' for i in range(Nb_all_sensors)]
sensor_types_nb = list(range(0)) # list of integer for [#TE,#PT,#DCV,#pyro...]

Nb_of_PlotWindows = 0
# takes account of separate plot for arduino(s) heating status
# = Nb_of_PlotWindows - Nb_of_Additional_Arduino_Plots

daq_sensor_types = list(range(0)) # for special parameter like LSYNC, OCOM, ...
daq_gr_list = list(range(0))

Nb_of_TE = sensor_list.count('TE')
if Nb_of_TE != 0:
    sensor_types_nb.append(Nb_of_TE)
    sensor_types.append('TE')
    daq_gr_list.append(Nb_of_PlotWindows)
    Nb_of_PlotWindows += 1
    daq_sensor_types.append('TE')

Nb_of_PT = sensor_list.count('PT')
if Nb_of_PT != 0:
    sensor_types_nb.append(Nb_of_PT)
    sensor_types.append('PT')
    daq_gr_list.append(Nb_of_PlotWindows)
    Nb_of_PlotWindows += 1
    if '100' in range_list:
        daq_sensor_types.append('PT-100')
    if '1000' in range_list:
        daq_sensor_types.append('PT-1000')
if Nb_of_TE != 0 or Nb_of_PT !=0:
    Nb_Instruments += 1
    instruments_list.append('DAQ-6510-Temperatures')

Nb_of_Rogowski = sensor_list.count('Rogowski')
if Nb_of_Rogowski != 0:
    Nb_Instruments += 1
    instruments_list.append('DAQ-6510-Rogowski')
    sensor_types_nb.append(Nb_of_Rogowski)
    sensor_types.append('Rogowski')
    daq_gr_list.append(Nb_of_PlotWindows)
    Nb_of_PlotWindows += 1
    daq_sensor_types.append('Rogowski')    

Nb_of_DCV = sensor_list.count('DCV')    
Nb_of_100mV = 0
Nb_of_Volt = 0
if Nb_of_DCV != 0:
    Nb_of_100mV = range_list.count('100mV')
    if Nb_of_100mV != 0:
        Nb_Instruments += 1
        instruments_list.append('DAQ-6510-DCV-100mV')
        sensor_types_nb.append(Nb_of_100mV)
        sensor_types.append('DCV-100mV')
        daq_gr_list.append(Nb_of_PlotWindows)
        Nb_of_PlotWindows += 1
        daq_sensor_types.append('DCV-100mV')
    Nb_of_Volt = Nb_of_DCV - Nb_of_100mV
    if Nb_of_Volt != 0:
        Nb_Instruments += 1
        instruments_list.append('DAQ-6510-DCV-V')
        sensor_types_nb.append(Nb_of_Volt)
        sensor_types.append('DCV')
        daq_gr_list.append(Nb_of_PlotWindows)
        Nb_of_PlotWindows += 1
        daq_sensor_types.append('DCV')

Nb_of_ACV = sensor_list.count('ACV')    
if Nb_of_ACV != 0:
    Nb_Instruments += 1
    instruments_list.append('DAQ-6510-ACV')
    sensor_types_nb.append(Nb_of_ACV)
    sensor_types.append('ACV')
    daq_gr_list.append(Nb_of_PlotWindows)
    Nb_of_PlotWindows += 1
    daq_sensor_types.append('ACV')

Nb_of_DAQ_sensors = Nb_of_TE + Nb_of_PT + Nb_of_ACV + Nb_of_DCV + Nb_of_Rogowski
Nb_of_DAQ_sensor_types = len(daq_sensor_types)    

if Pyro_present:
    # add pyrometer(s) as virtual channels 
    pyro_gr_list = list(range(0)) 
    # list to plot each pyrometer in a separate plot window
    # starts with the first available plot window
    sensor_types_nb.append(Nb_of_Pyrometer)
    sensor_types.append('Pyro')
    
    pyro_t90_time = list(range(0))
    for i in range(Nb_of_Pyrometer):
        sensor_list.append('Pyro')
        range_list.append('--')
        pyro_gr_list.append(Nb_of_PlotWindows)
        Nb_of_PlotWindows += 1
        p = int(pyro_t90_list[i])-1
        v = pyro_t90_times[i][p].replace(',', '')
        #print (p, v)
        pyro_t90_time.append(v)

if Pyro_array_present:
    # add pyrometer array as virtual channels
    pyro_array_gr_list = list(range(0))
    pyro_array_t90_time = list(range(0))
    Nb_of_pyro_array_heads = len(pyro_array_alias_list)
    sensor_types.append('Pyro_head')
    sensor_types_nb.append(Nb_of_pyro_array_heads)
    pyro_array_gr_list.append(Nb_of_PlotWindows)
    Nb_of_PlotWindows += 1
    for i in range(Nb_of_pyro_array_heads):
        sensor_list.append('Pyro_head')
        range_list.append('--')
        #pyro_array_gr_list.append(Nb_of_PlotWindows)
        #Nb_of_PlotWindows += 1
        p = int(pyro_array_t90_list[i])-1
        v = pyro_array_t90_times[i][p].replace(',', '')
        #print (p, v)
        pyro_array_t90_time.append(v)
            

if Arduino_present:    
    # add arduino(s) as virtual channels    
    arduino_gr_list = list(range(0))
    # list to plot each arduino in a separate plot window
    # starts with the first available plot window
    sensor_types_nb.append(Nb_of_Arduino)
    sensor_types.append('Arduino')
    arduino_last_channel = arduino_ch_list[0]
    arduino_heating_command = 'h'
    for j in range(len(arduino_ch_list)):
        arduino_active_channel = arduino_ch_list[j]
        sensor_list.append('Arduino')
        range_list.append('--')
        if arduino_cmd_list[j] == arduino_heating_command or arduino_active_channel[0:2] != arduino_last_channel[0:2]:
            Nb_of_PlotWindows += 1        
        arduino_gr_list.append(Nb_of_PlotWindows)
        arduino_last_channel = arduino_active_channel
    Nb_of_PlotWindows += 1
    Nb_of_Additional_Arduino_Plots = arduino_cmd_list.count(arduino_heating_command)
        

for i in range(Nb_all_sensors):
    if sensor_list[i] == 'Rogowski':
        sensor_unit_list[i] = 'V'
    if sensor_list[i] == 'DCV' and range_list[i] != '100mV':
        sensor_unit_list[i] = 'V'
    if sensor_list[i] == 'DCV' and range_list[i] == '100mV':
        sensor_list[i] = 'DCV-100mV'
        #sensor_unit_list[i] = 'mV'
        sensor_unit_list[i] = 'V'
for i in range(len(daq_sensor_list)):
    if daq_sensor_list[i] == 'DCV' and daq_range_list[i] == '100mV':
        daq_sensor_list[i] = 'DCV-100mV'   

print ('number of instruments: ', Nb_Instruments)
print ('Instruments: ', instruments_list)
print ('Number of all sensors: ', Nb_all_sensors)
print ('Active channel list: ', ch_list)
print ('Active sensor list: ', sensor_list)
print ('Active sensor range list:', range_list)
print ('Sensor measurements unit: ', sensor_unit_list)
print ('Sensor alias list: ', alias_list)
print ('Sensor types: ', sensor_types)
Nb_sensor_types = len(sensor_types_nb)
print ('Number of sensor types: ', Nb_sensor_types)
print ('sensor types number: ', sensor_types_nb)
print ('Channel * factors: ', factor_list)
print ('Channel offsets: ', offset_list)


if DAQ_present:
    print ('\n===============================')
    print ('Setting up Keithley DAQ-6510...')
    print ('===============================')
    print ('Keithley DAQ-6510 @ COM -', daq_com, ' : ', daq_rate, ', ', daq_bits, ', ', daq_stop, ', ', daq_parity)
    print ('DAQ overflow value: ', daq_overflow)
    print ('DAQ alias list: ', daq_alias_list)
    print ('DAQ sensor types: ', daq_sensor_types)
    print ('number of DAQ sensors: ', Nb_of_DAQ_sensors)
    print ('DAQ graphics list: ', daq_gr_list)
    
    if args.nplc is not None:
        print ('Setting overall NPLC to: ', args.nplc)
        for i in range(len(daq_nplc_list)):
            daq_nplc_list[i] = str(args.nplc)
    print ('DAQ NPLC(s): ', daq_nplc_list)
    print ('Overall LSYNC is: ', DAQ_lsync)
    print ('Overall OCOM is: ', DAQ_ocom)
    print ('Overall AZER is: ', DAQ_azer)
    print ('Overall ADEL is: ', DAQ_adel)
    
    
    DAQ_6510.init_daq(daq_com, daq_rate, daq_bits, daq_stop, daq_parity, args.debug_daq, args.test, args.time)
    DAQ_6510.reset_daq()
    DAQ_6510.idn_daq()
    DAQ_6510.idn_card_1()
    DAQ_6510.idn_card_2()
    DAQ_6510.config_daq(daq_ch_list, daq_alias_list, daq_sensor_list, daq_range_list, daq_sensor_types, daq_nplc_list, \
                        PT_1000_mode, DAQ_lsync, DAQ_ocom, DAQ_azer, DAQ_adel) 
    

if Pyro_present:
    print ('\n==========================')
    print ('Setting up pyrometer(s)...')
    print ('==========================')
    print ('Pyro overflow value: ', pyro_overflow)
    print ('Pyro com ports: ', pyro_com_list)
    print ('Pyro alias list: ', pyro_alias_list)
    print ('Pyro transmissions: ', pyro_tr_list)
    print ('Pyro emissions: ', pyro_em_list)
    print ('Pyro datarate: ', pyro_rate_list)
    print ('Pyro bits: ', pyro_bits_list)
    print ('Pyro stop: ', pyro_stop_list)
    print ('Pyro parity: ', pyro_parity_list)
    print ('Pyro t90: ', pyro_t90_list, pyro_t90_time)
    print ('Pyro card(s) list: ', pyro_card_list)
    print ('Pyro graphics list: ', pyro_gr_list)
    
    for i in range(Nb_of_Pyrometer):
        print ('Init Pyro ', i+1)
        Pyrometer.Init_Pyro(i, pyro_com_list[i], pyro_rate_list[i], pyro_bits_list[i], \
                            pyro_stop_list[i], pyro_parity_list[i], args.debug_pyro, args.test)        
        print ('Config Pyro ', i+1)
        Pyrometer.Config_Pyro(i, pyro_em_list[i], pyro_tr_list[i])
        if not args.test:
            pyro_model_list.append(Pyrometer.Get_ID(i))
            print ('distance=')
            print (str(Pyrometer.Get_Focus(i))[-4:])
            focus = int(str(Pyrometer.Get_Focus(i))[-4:])
            pyro_distance_list.append(str(focus))
        else:
            focus_str = '02000390'
            focus = int(focus_str[-4:])
            pyro_model_list.append('xxx')
            pyro_distance_list.append(str(focus))
        
        #print (str(pyro_t90_times[i]).replace('[','').replace(']','').replace(',','').replace("'",'').split())
        #print (len(str(pyro_t90_times[i]).replace('[','').replace(']','').replace(',','').replace("'",'').split()))
            
    print ('Pyro model list: ', pyro_model_list)
    

if Pyro_array_present:
    print ('\n==========================')
    print ('Setting up pyrometer array...')
    print ('==========================')
    print ('Pyro array overflow value: ', pyro_overflow)
    print ('Pyro array COM port: ', pyro_array_com)
    print ('Pyro array datarate: ', pyro_array_rate)
    print ('Pyro array bits: ', pyro_array_bits)
    print ('Pyro array stop: ', pyro_array_stop)
    print ('Pyro array parity: ', pyro_array_parity)    
    print ('Pyro array alias list: ', pyro_array_alias_list)
    print ('Pyro array emissions: ', pyro_array_em_list)
    print ('Pyro array t90: ', pyro_array_t90_list, pyro_array_t90_time)
    print ('Pyro array array card: ', pyro_array_card_list)
    print ('Pyro array graphics list: ', pyro_array_gr_list) 
    
    print ('Init Pyro Array')
    Pyrometer_Array.Init_Pyro_Array(pyro_array_com, pyro_array_rate, pyro_array_bits, pyro_array_stop, \
                        pyro_array_parity, args.debug_array, args.test)        
    print ('Config Pyro Array')
    for i in range(Nb_of_pyro_array_heads):
        if not args.test:
            Pyrometer_Array.Config_Pyro_Array(i, pyro_array_em_list[i])
            pyro_array_model_list.append(Pyrometer_Array.Get_head_ID(i))
        else:
            pyro_array_model_list.append('xxx')
        
    print ('Pyro Array model list: ', pyro_array_model_list)
            
if Arduino_present:
    print ('\n==========================')
    print ('Setting up Arduino(s)...')
    print ('==========================') 
    print ('Arduino overflow value: ', arduino_overflow)
    print ('Arduino com port(s): ', arduino_com_list)
    print ('Arduino rate(s): ', arduino_rate_list)
    print ('Arduino bit(s): ', arduino_bits_list)
    print ('Arduino stop(s): ', arduino_stop_list)
    print ('Arduino parity(s): ', arduino_parity_list)
    print ('Arduino card(s) list: ', arduino_card_list)
    print ('Arduino channel list: ', arduino_ch_list)
    print ('Arduino alias list: ', arduino_alias_list)
    print ('Arduino command list: ', arduino_cmd_list)
    print ('Arduino read-id list: ', arduino_read_id_list)
    print ('Arduino end-id list: ', arduino_end_id_list)
    print ('Arduino position list: ', arduino_position_list)
    print ('Arduino separator list: ', arduino_separator_list)
    print ('Arduino graphics list: ', arduino_gr_list)
    
    for i in range(Nb_of_Arduino):
        print ('Init Arduino: ', i+1)
        Arduino.Init_Arduino(i, arduino_com_list[i], arduino_rate_list[i], arduino_bits_list[i],\
                            arduino_stop_list[i], arduino_parity_list[i], args.debug_arduino, args.test)    
    
    arduino_first_channel = arduino_ch_list[0]

# create the graphics index, means the correct graphics window for each sensor or sensor type
# sensor type heating status from arduino needs also extra window
gr_idx = list(range(Nb_all_sensors))
for i in range(Nb_sensor_types):
    z = 0
    z1 = 0
    z2 = 0
    for j in range(Nb_all_sensors):
        if sensor_list[j] == sensor_types[i]:
            gr_idx[j] = i
        if sensor_list[j] == 'Pyro':
            gr_idx[j] = pyro_gr_list[z]
            z += 1
        if sensor_list[j] == 'Pyro_head':
            gr_idx[j] = pyro_array_gr_list[z1]
            #z1 += 1        
        if sensor_list[j] == 'Arduino':
            gr_idx[j] = arduino_gr_list[z2]
            z2 += 1
            
            
# and begin the colors list for each new graphics window again
color_list = list(range(Nb_all_sensors))
for z in range(Nb_of_PlotWindows):
    indices = [i for i, x in enumerate(gr_idx) if x == z]
    k = 0
    for j in range(len(indices)):
        color_list[indices[j]] = k
        k += 1

print ('\n \n')
print ('number of PlotWindows: ', Nb_of_PlotWindows) 
if Arduino_present:
    print ('number of additional Arduino plots: ', Nb_of_Additional_Arduino_Plots)
   
print ('graphics index: ', gr_idx)
print ('colors list: ', color_list)
print ('\n')

#===========================================
def Init_Output_File(ch):
#===========================================
# Init data file output
# Init online protocol
    
    global FileOutName, ProtocolFileName
    
    actual_date = datetime.datetime.now().strftime('%Y_%m_%d')    
    FileOutPrefix = actual_date
    FileOutIndex = str(1).zfill(2)
    FileOutName = ''    
    
    FileOutName = FileOutPrefix + '_#' + FileOutIndex + '.dat'
    ProtocolFileName = FileOutPrefix + '_#' + FileOutIndex + '_op.txt'
    j = 1
    while os.path.exists(FileOutName) :
        j = j + 1
        FileOutIndex = str(j).zfill(2)
        FileOutName = FileOutPrefix + '_#' + FileOutIndex + '.dat'
        ProtocolFileName = FileOutPrefix + '_#' + FileOutIndex + '_op.txt' 
    print ('Output data: ', FileOutName)   
    print ('Online Protocol: ', ProtocolFileName)
    OutputFile = open(FileOutName, 'w')
    # write sensor list
    OutputFile.write('Sensor list\n') 
    OutputFile.write(str(ch_list) + '\n')
    OutputFile.write('Alias list\n')
    OutputFile.write(str(alias_list) + '\n')
    OutputFile.write(str(sensor_list) + '\n')
    OutputFile.write(str(range_list) + '\n')
    OutputFile.write('--------------------------------\n')        
    OutputFile.write('time')
    OutputFile.write('time'.rjust(16))
    for j in range(Nb_all_sensors):
        OutputFile.write((ch[j]).rjust(14))
        if sensor_list[j] == 'PT' and range_list[j] == '1000' and PT_1000_mode == 'R+T':
            OutputFile.write((ch[j]).rjust(14))
    OutputFile.write('\n')
    OutputFile.write('abs.')
    OutputFile.write('s'.rjust(16))
    for j in range(Nb_all_sensors):
        if sensor_list[j] == 'PT' and range_list[j] == '1000' and PT_1000_mode == 'R+T':
            OutputFile.write('°C'.rjust(14))
            OutputFile.write('Ohm'.rjust(14))
        elif sensor_list[j] == 'PT' and range_list[j] == '1000' and PT_1000_mode == 'R':
            OutputFile.write('Ohm'.rjust(14))
        elif sensor_list[j] == 'Rogowski':
            OutputFile.write('A'.rjust(14))
        else:
            OutputFile.write(sensor_unit_list[j].rjust(14))
            
    OutputFile.write('\n')
    OutputFile.close(    )
    
    ProtocolFile = open(ProtocolFileName, 'w')
    ProtocolFile.write('Online protocol for: ' + FileOutName + '\n')
    ProtocolFile.write('=========================================\n')
    
    ProtocolFile.write('Sampling with: dt[ms]=' + str(Sampling_Timer) + '\n')
    if DAQ_present:
        ProtocolFile.write('\nStarting values for DAQ:\n')
        ProtocolFile.write('LSYNC for all DAQ-channels: ' + str(DAQ_lsync) + '\n')
        ProtocolFile.write('OCOM for all DAQ-channels: ' + str(DAQ_ocom) + '\n')
        ProtocolFile.write('AZER for all DAQ-channels: ' + str(DAQ_azer) + '\n')
        ProtocolFile.write('ADEL for all DAQ-channels: ' + str(DAQ_adel) + '\n')
        
        for i in range(Nb_of_DAQ_sensors):
            ProtocolFile.write(daq_alias_list[i] + ' : ' + 'NPLC=' + daq_nplc_list[i] + ', ' \
                               + 'sensor=' + daq_sensor_list[i] + ', ' + 'type=' + daq_range_list[i] +'\n')
    
    if Pyro_present:
        ProtocolFile.write('\nStarting values for pyrometer:\n')
        for i in range(Nb_of_Pyrometer):
            ProtocolFile.write('Pyrometer ' + str(i+1) + ' : ' + pyro_alias_list[i] + ', ' + pyro_model_list[i] + ', ' + 'emission=' + pyro_em_list[i] +  '%' + ', ' + 'transmission=' + pyro_tr_list[i] +  '%' \
                               + ', ' + 't90=' + pyro_t90_time[i] + 's' + ', ' + 'distance=' + pyro_distance_list[i] + 'mm' + '\n')
    
    if Pyro_array_present:
        ProtocolFile.write('\nStarting values for pyrometer-array:\n')
        for i in range(Nb_of_pyro_array_heads):
            ProtocolFile.write('Head ' + str(i+1) + ' : ' + pyro_array_alias_list[i] + ', ' + pyro_array_model_list[i] \
                               + ', ' + 'emission=' + pyro_array_em_list[i] +  '%' \
                               + ', ' + 't90=' + pyro_array_t90_time[i] + 's' + '\n')
                               
                
            
    ProtocolFile.write('\nstarting with measurements....')
    ProtocolFile.write('\n----------------------------\n')
            
    ProtocolFile.close()
    
#===========================================
def calc_temp_PT1000(r):
#===========================================
    a = 3.9083E-3
    b = -0.5775E-6
    d = a**2 - 4*b*(1-r/1000)
    temp = (-a+np.sqrt(d))/2/b
    return (temp)


#===========================================
def get_measurements():
#===========================================
# Get the sampled data from the active instrument(s)  
    data = list(range(0))
    data_ohm = list(range(0)) # ohm values from PT-1000
    
    if DAQ_present:
        # comma separated string: channel,reading,channel,reading, .....
        m = DAQ_6510.get_daq()
        if args.time:
            print (m,'\n')
        m_list = m.split(',')
        if args.time:
            step = 3 # with timestamp
        else:
            step = 2 # without timestamp
        for i in range(0, len(m_list)-1, step):
            if m_list[i] != daq_ch_list[int(i/step)]:
                print ('Error in Keithley channels....')
            if sensor_list[int(i/step)] == 'PT' and range_list[int(i/step)] == '1000':
                # 'R': ohm value
                # 'T': temp value calculated by the DAQ
                # 'R+T': ohm value, must be calculated by the own function
                if PT_1000_mode == 'R':
                    val_R = float(m_list[i+step-1])
                    if val_R >= daq_overflow:
                        print ('Overflow from DAQ')
                        val_R = np.nan                    
                    data.append(val_R)
                if PT_1000_mode == 'R+T':
                    val_R = float(m_list[i+step-1])
                    val_T = round(calc_temp_PT1000(val_R), 3)
                    if val_R >= daq_overflow:
                        print ('Overflow from DAQ')
                        val_R = np.nan
                        val_T = np.nan
                    data.append(val_T)
                    data_ohm.append(val_R)
                if PT_1000_mode == 'T':
                    val_T = float(m_list[i+step-1])
                    if val_T >= daq_overflow:
                        print ('Overflow from DAQ')
                        val_T = np.nan                                 
                    data.append(val_T)
            else:
                val = round(float(m_list[i+step-1]), 6)
                if val >= daq_overflow:
                    print ('Overflow from DAQ')
                    val = np.nan
                data.append(val)
        
    if Pyro_present:
        for i in range(Nb_of_Pyrometer):
            val = Pyrometer.Read_Pyro(i)
            val = round(val, 3)
            if val >= pyro_overflow:
                print ('Overflow from Pyrometer number ', i+1)
                val = np.nan
            data.append(val)
    
    if Pyro_array_present:
        for i in range(Nb_of_pyro_array_heads):
            val = Pyrometer_Array.Read_Pyro_Array(i)
            val = round(val, 3)
            if val >= pyro_overflow:
                print ('Overflow from Pyrometer-Array head number ', i+1)
                val = np.nan
            data.append(val)            
            
    if Arduino_present:
        nb1 = 0
        for i in range(Nb_of_Arduino):
            nb2 = nb1
            for j in range(len(arduino_ch_list)):
                if arduino_card_list[i][5:] == arduino_ch_list[j][:2]:
                    nb2 += 1
            result = Arduino.Read_Arduino(i, arduino_cmd_list[nb1:nb2], arduino_read_id_list[nb1:nb2], \
                                          arduino_end_id_list[nb1:nb2], arduino_position_list[nb1:nb2], \
                                          arduino_separator_list[nb1:nb2]) 
            nb1 = nb2
            val = round(val,3)
            for z, val in enumerate(result):
                if val >= arduino_overflow:
                    print ('Overflow from Arduino number ', i+1)
                    val = np.nan
                data.append(val)
    return [data, data_ohm]

    
def Graphics():
    # ====================================================
    # main loop of the GUI
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    
    global time_start, sampling_started
    time_start = datetime.datetime.now()
    sampling_started = False
    
    # scaling initialisations
    x_min = 0 # bottom x-axis scaling
    x_max = 60
    y_min = 0 # temperature scaling
    y_max = 20    
    x2_list = []
    x2_ticks = [] # init ticks
    x2_Nb_ticks = 4 # show everytime ? ticks at top x axis
    delta_t = int(x_max - x_min)
    
    for i in range(x2_Nb_ticks):
        x2_list.append((datetime.datetime.now() + datetime.timedelta(seconds=i*delta_t/(x2_Nb_ticks-1))).strftime('%H:%M:%S'))
        x2_ticks.append([i*delta_t/(x2_Nb_ticks-1), x2_list[i]])    
    
    tab_list = list(range(0))
    tab_daq_TE_PT = 'Temperatures'
    tab_daq_Rogowski = 'Rogowski'
    tab_daq_100mV = 'DCV 100mV'
    tab_daq_Volt = 'DCV Volt'
    tab_daq_ACV = 'ACV Volt'
    tab_pyro = 'Pyrometer(s)'
    tab_pyro_array = 'Pyro-array'
    tab_arduino = 'Arduino(s)'
    tab_misc_para = 'other parameter'
   
    if DAQ_present:
        if Nb_of_TE != 0 or Nb_of_PT !=0:
            tab_list.append(tab_daq_TE_PT)
        if Nb_of_Rogowski != 0:
            tab_list.append(tab_daq_Rogowski)
        if Nb_of_100mV != 0:
            tab_list.append(tab_daq_100mV)            
        if Nb_of_Volt != 0:
            tab_list.append(tab_daq_Volt)            
        if Nb_of_ACV != 0:
            tab_list.append(tab_daq_ACV)
    if Pyro_present:
        tab_list.append(tab_pyro)
    if Pyro_array_present:
        tab_list.append(tab_pyro_array)    
    if Arduino_present:
        tab_list.append(tab_arduino)
    #tab_list.append(tab_misc_para)
    
    print ('Number of tabs: ', len(tab_list))
    
    class grPanel(QWidget):
        pdg = 0.0
        
        def __init__(self, parent=None):
            
            class QHLine(QFrame):
                def __init__(self):
                    super(QHLine, self).__init__()
                    self.setFrameShape(QFrame.HLine)
                    self.setFrameShadow(QFrame.Sunken)                
            
            class LineEdit(QLineEdit):
                def __init__(self, parent = None):
                    super(LineEdit, self).__init__(parent)
                def focusInEvent(self, e):
                    super(LineEdit, self).focusInEvent(e)
                    self.setStyleSheet('color: red')
                    self.selectAll()
                def mousePressEvent(self, e):
                    self.setStyleSheet('color: red')
                    self.selectAll() 
                #def focusOutEvent(self, e):
                    #super(LineEdit, self).focusOutEvent(e)
                    #self.deselect()
                    #self.setStyleSheet('color: black')
                    
            super(grPanel, self).__init__(parent)  
            
            self.myPen = list(range(20))
            self.mycolors = ['red','green','cyan','magenta','blue','orange','darkmagenta','yellow','turquoise','purple','brown','tomato','lime','olive','navy','darkmagenta','beige','peru','grey','white']
            
            for i in range(20):
                self.myPen[i] = pg.mkPen(color=matplotlib.colors.cnames[self.mycolors[i]])
                #self.myPen[i] = pg.mkPen(color=(i,20))
            
                        
            # each row is a sampled time step
            self.pData_time = np.zeros((0, 2)) # Dim-0 = time/abs, Dim-1=time/s
            self.pData_temp = np.empty((0, Nb_all_sensors)) # following Dim's are temperatures   
            
            # graphics for TE, PT, DCV, ....
            #self.canvas = [myGraphics() for i in range(Nb_Instruments)]
            #self.canvas = [pg.GraphicsLayoutWidget() for i in range(Nb_Instruments)]
            self.canvas = [pg.GraphicsWindow() for i in range(Nb_Instruments)]
            self.gr = list(range(Nb_of_PlotWindows)) 
            self.pData_line = list(range(Nb_all_sensors))
            self.ax_X = list(range(Nb_of_PlotWindows)) # axis object from the plot (bottom)
            self.ax_X_2 = list(range(Nb_of_PlotWindows)) # axis object from the plot (top)
            self.ax_Y = list(range(Nb_of_PlotWindows)) # axis object from the plot (left)          
      
            for i in range(Nb_sensor_types):
                if sensor_types[i] == 'TE' or sensor_types[i] == 'PT':# or sensor_types[i]== 'DCV' or sensor_types[i] == 'ACV':
                    tab_idx = tab_list.index(tab_daq_TE_PT)
                if sensor_types[i] == 'Rogowski':
                    tab_idx = tab_list.index(tab_daq_Rogowski)
                if sensor_types[i] == 'DCV-100mV':
                    tab_idx = tab_list.index(tab_daq_100mV)
                if sensor_types[i] == 'DCV':
                    tab_idx = tab_list.index(tab_daq_Volt)
                if sensor_types[i] == 'ACV':
                    tab_idx = tab_list.index(tab_daq_ACV)
                if sensor_types[i] == 'Pyro':
                    tab_idx = tab_list.index(tab_pyro)
                if sensor_types[i] == 'Pyro_head':
                    tab_idx = tab_list.index(tab_pyro_array)                    
                if sensor_types[i] == 'Arduino':
                    tab_idx = tab_list.index(tab_arduino)
                    
                # create each sensor type in a separate plot window
                if sensor_types[i] == 'Pyro':
                    # for more than one pyrometer each one in a seperate plot
                    for j in range(Nb_of_Pyrometer):
                        idx = pyro_gr_list[j]
                        self.gr[idx] = self.canvas[tab_idx].addPlot(j, 0)
                        self.gr[idx].setXRange(x_min, x_max, padding=self.pdg)
                        self.gr[idx].setYRange(y_min, y_max, padding=self.pdg) 
                        self.gr[idx].setLabel('left', 'temp [°C]', color='red')
                        self.gr[idx].setLabel('bottom', 'time [s]')
                        self.gr[idx].setLabel('top')
                        self.gr[idx].setLabel('right', '')
                        self.gr[idx].showGrid(x=True, y=True)
                        self.ax_X[idx] = self.gr[idx].getAxis('bottom')
                        self.ax_Y[idx] = self.gr[idx].getAxis('left')
                        self.ax_X_2[idx] = self.gr[idx].getAxis('top')
                        self.ax_X_2[idx].setTicks([x2_ticks,[]]) 
                else:
                    if sensor_types[i] == 'Pyro_head':
                        for j in range(len(pyro_array_gr_list)):
                            idx = pyro_array_gr_list[j]
                            self.gr[idx] = self.canvas[tab_idx].addPlot(j, 0)
                            self.gr[idx].setXRange(x_min, x_max, padding=self.pdg)
                            self.gr[idx].setYRange(y_min, y_max, padding=self.pdg)
                            self.gr[idx].setLabel('left', 'temp [°C]', color='red')
                            self.gr[idx].setLabel('bottom', 'time [s]')
                            self.gr[idx].setLabel('top')
                            self.gr[idx].setLabel('right', '')
                            self.gr[idx].showGrid(x=True, y=True)
                            self.ax_X[idx] = self.gr[idx].getAxis('bottom')
                            self.ax_Y[idx] = self.gr[idx].getAxis('left')
                            self.ax_X_2[idx] = self.gr[idx].getAxis('top')
                            self.ax_X_2[idx].setTicks([x2_ticks,[]])                             
                    else:
                        if sensor_types[i] == 'Arduino':
                            # for more than one arduino each one in a seperate plot
                            # arduino with sensor type heat status also in a separate plot
                            previous_index = arduino_gr_list[0]
                            for j in range(len(arduino_gr_list)):
                                idx = arduino_gr_list[j]
                                if j == 0 or idx != previous_index:
                                    self.gr[idx] = self.canvas[tab_idx].addPlot(j, 0)
                                    self.gr[idx].setMouseEnabled(x = False, y = False)
                                    self.gr[idx].setXRange(x_min, x_max, padding=self.pdg)
                                    self.gr[idx].setYRange(y_min, y_max, padding=self.pdg) 
                                    if arduino_cmd_list[j] == arduino_heating_command:
                                        self.gr[idx].setLabel('left', 'heating ON / OFF', color='green')
                                    else:
                                        self.gr[idx].setLabel('left', 'temp [°C]', color='red')
                                    self.gr[idx].setLabel('bottom', 'time [s]')
                                    self.gr[idx].setLabel('top')
                                    self.gr[idx].setLabel('right', '')
                                    self.gr[idx].showGrid(x=True, y=True)
                                    self.ax_X[idx] = self.gr[idx].getAxis('bottom')
                                    self.ax_Y[idx] = self.gr[idx].getAxis('left')
                                    self.ax_X_2[idx] = self.gr[idx].getAxis('top')
                                    self.ax_X_2[idx].setTicks([x2_ticks,[]])
                                previous_index = idx
                        else:
                            self.gr[i] = self.canvas[tab_idx].addPlot(i, 0)
                            self.gr[i].setXRange(x_min, x_max, padding=self.pdg)
                            self.gr[i].setYRange(y_min, y_max, padding=self.pdg)
                            self.gr[i].setLabel('left', 'temp [°C]', color='red')
                            if sensor_types[i] == 'Rogowski':
                                self.gr[i].setLabel('left', 'current [A]', color='red')
                            if sensor_types[i] == 'DCV-100mV':
                                self.gr[i].setLabel('left', 'voltage [V]', color='red')
                            if sensor_types[i] == 'DCV':
                                self.gr[i].setLabel('left', 'voltage [V]', color='red')
                            if sensor_types[i] == 'ACV':
                                self.gr[i].setLabel('left', 'voltage [V]', color='red')                        
                            self.gr[i].setLabel('bottom', 'time [s]')
                            self.gr[i].setLabel('top')
                            self.gr[i].setLabel('right', '')
                            self.gr[i].showGrid(x=True, y=True)
                            self.ax_X[i] = self.gr[i].getAxis('bottom')
                            self.ax_Y[i] = self.gr[i].getAxis('left')
                            self.ax_X_2[i] = self.gr[i].getAxis('top')
                            self.ax_X_2[i].setTicks([x2_ticks,[]])                
                
            x = self.pData_time[:,0]
            for i in range(Nb_all_sensors):
                # begin the colors list for each new graphics window again
                y = self.pData_temp[:, gr_idx[i]]
                self.pData_line[i] = self.gr[gr_idx[i]].plot(x, y, pen=self.myPen[color_list[i]])
                
            
            # init timer for the sampling
            self.timer = QTimer()
            self.timer.setInterval(Sampling_Timer)
            self.timer.timeout.connect(self.update_graphics)            
            
            self.btn_Start = QPushButton()
            self.btn_Start.setText('Start')
            self.btn_Start.setMaximumWidth(300)
            self.btn_Start.setIcon(QIcon('Start-icon.png'))
            self.btn_Start.setFont(QFont('Times', 16, QFont.Bold))
            self.btn_Start.setStyleSheet('color: red')
            self.btn_Start.setEnabled(True)
            
            self.btn_Pause = QPushButton()
            self.btn_Pause.setText('Pause')
            self.btn_Pause.setMaximumWidth(300)
            self.btn_Pause.setIcon(QIcon('Pause-icon.png'))
            self.btn_Pause.setFont(QFont('Times', 16, QFont.Bold))
            self.btn_Pause.setStyleSheet('color: red')
            self.btn_Pause.setEnabled(False)

            self.btn_Exit = QPushButton()
            self.btn_Exit.setText('Exit')
            self.btn_Exit.setMaximumWidth(380)
            self.btn_Exit.setIcon(QIcon('Exit-icon.png'))
            self.btn_Exit.setFont(QFont('Times', 16, QFont.Bold))
            self.btn_Exit.setStyleSheet('color: red')
            self.btn_Exit.setEnabled(True)
            
            self.lbl_1_current_time = QLabel('time: ')
            self.lbl_1_current_time.setFont(QFont('Times', 14))
            self.lbl_1_current_time.setStyleSheet('color: black')
            self.lbl_2_current_time = QLabel('xx')
            self.lbl_2_current_time.setFont(QFont('Times', 14, QFont.Bold))  
            self.lbl_2_current_time.setStyleSheet('color: blue')
            self.lbl_1_start_sampling_time = QLabel('started : ')
            self.lbl_1_start_sampling_time.setFont(QFont('Times', 14))
            self.lbl_1_start_sampling_time.setStyleSheet('color: black')
            self.lbl_2_start_sampling_time = QLabel('xx')
            self.lbl_2_start_sampling_time.setFont(QFont('Times', 14))   
            self.lbl_2_start_sampling_time.setStyleSheet('color: red')   
            self.lbl_file_name = QLabel('filename: ')
            self.lbl_file_name.setFont(QFont('Times', 14))
            self.lbl_file_name.setStyleSheet('color: black')
            self.file_name = QLabel('xxx')
            self.file_name.setFont(QFont('Times', 14))
            self.file_name.setStyleSheet('color: red')            
                
            MainLayout = QVBoxLayout() 
            self.setLayout(MainLayout)
            
            ButtonLayout = QHBoxLayout()
            GraphicsLayout = [QVBoxLayout() for i in range(Nb_Instruments)]
            ParameterLayout = [QVBoxLayout() for i in range(Nb_Instruments)]
            ParameterGroupLayout = list(range(Nb_of_PlotWindows))
            for i in range(Nb_of_PlotWindows):
                # layout inside the specific sensor type (TE, PT, DCV, ...)
                ParameterGroupLayout[i] = QGridLayout()
            
            Graphics = [QWidget() for i in range(Nb_Instruments)]
            for i in range(Nb_Instruments):
                Graphics[i].setLayout(GraphicsLayout[i])
            
            Parameter = [QWidget() for i in range(Nb_Instruments)]
            for i in range(Nb_Instruments):
                Parameter[i].setLayout(ParameterLayout[i])
            Parameter_Group = list(range(Nb_of_PlotWindows))  
            for i in range(Nb_of_PlotWindows):
                idx = gr_idx.index(i)
                Parameter_Group[i] = QGroupBox(sensor_list[idx])
                if sensor_list[idx] == 'Arduino':
                    group_name = 'Arduino - ' + str(int(ch_list[idx][0:2])-9)
                    Parameter_Group[i] = QGroupBox(group_name)
                if sensor_list[idx] == 'Pyro':
                    group_name = alias_list[idx]
                    Parameter_Group[i] = QGroupBox(group_name)
                if sensor_list[idx] == 'Pyro_head':
                    group_name = 'Pyro-array' #alias_list[idx]
                    Parameter_Group[i] = QGroupBox(group_name)                   
                Parameter_Group[i].setObjectName('Group')
                Parameter_Group[i].setStyleSheet('QGroupBox#Group{border: 1px solid black; color: black; \
                                         font-size: 16px; subcontrol-position: top left; font-weight: bold;\
                                         subcontrol-origin: margin; padding: 10px}')   
            for i in range(Nb_of_PlotWindows):
                Parameter_Group[i].setLayout(ParameterGroupLayout[i])     
                
            Button = QWidget() 
            Button.setLayout(ButtonLayout)
            
            SplitterStylesheet = "QSplitter::handle{background: LightGrey; width: 5px; height: 5px;}"
            Splitter_Display = QSplitter(Qt.Vertical,frameShape=QFrame.StyledPanel) ## trennt die Hauptbereiche wie Graphics+Parameter und HauptButtons
            Splitter_Display.setChildrenCollapsible(False)
            Splitter_Display.setStyleSheet(SplitterStylesheet)   
            
            Splitter_Para_Display = [QSplitter(Qt.Horizontal,frameShape=QFrame.StyledPanel) for i in range(Nb_Instruments)]
            for i in range(Nb_Instruments):
                Splitter_Para_Display[i].setChildrenCollapsible(True)
                Splitter_Para_Display[i].setStyleSheet(SplitterStylesheet)    
            
            tabs = QTabWidget()
            tabs.setStyleSheet('QTabBar {font-size: 14pt; color: blue;}')
            tab = Splitter_Para_Display

            scroll = QScrollArea()
            scroll.setWidget(tabs)
            scroll.setWidgetResizable(True)
            screen_width  = gr_app.desktop().screenGeometry().width()
            screen_height  = gr_app.desktop().screenGeometry().height()
            if screen_width == 1280:
                scroll.setFixedHeight(850)
            else:
                scroll.setFixedHeight(1000)
            
            MainLayout.addWidget(Splitter_Display)
            Splitter_Display.addWidget(tabs)#(scroll)#(tabs)
            group = 0
            for i in range(Nb_Instruments):
                tabs.addTab(tab[i], tab_list[i])
                tab[i].addWidget(Graphics[i])
                tab[i].addWidget(Parameter[i])
                GraphicsLayout[i].addWidget(self.canvas[i])
                if tab_list[i] == tab_daq_TE_PT:
                    if 'TE' in sensor_types:
                        ParameterLayout[i].addWidget(Parameter_Group[group])
                        group += 1
                    if 'PT' in sensor_types:
                        ParameterLayout[i].addWidget(Parameter_Group[group])
                        group += 1
                if tab_list[i] == tab_daq_Rogowski:
                    if 'Rogowski' in sensor_types:
                        ParameterLayout[i].addWidget(Parameter_Group[group]) 
                        group += 1
                if tab_list[i] == tab_daq_100mV:
                    if 'DCV-100mV' in sensor_types:
                        ParameterLayout[i].addWidget(Parameter_Group[group]) 
                        group += 1
                if tab_list[i] == tab_daq_Volt:
                    if 'DCV' in sensor_types:
                        ParameterLayout[i].addWidget(Parameter_Group[group]) 
                        group += 1
                if tab_list[i] == tab_daq_ACV:
                    if 'ACV' in sensor_types:
                        ParameterLayout[i].addWidget(Parameter_Group[group]) 
                        group += 1
                if tab_list[i] == tab_pyro:
                    for j in range(Nb_of_Pyrometer):
                        ParameterLayout[i].addWidget(Parameter_Group[group])
                        group += 1
                if tab_list[i] == tab_pyro_array:
                    #for j in range(Nb_of_pyro_array_heads):
                    ParameterLayout[i].addWidget(Parameter_Group[group])
                    group += 1                
                if tab_list[i] == tab_arduino:
                    for j in range(Nb_of_Arduino + Nb_of_Additional_Arduino_Plots):
                        ParameterLayout[i].addWidget(Parameter_Group[group])
                        group += 1                    

                    
            various_parameter_Layout = QGridLayout()
            various_parameter = QWidget()
            various_parameter.setLayout(various_parameter_Layout)            
            #t_i = tab_list.index(tab_misc_para)
            #tabs.addTab(various_parameter, tab_list[t_i]) 
            
            self.edit_dt = LineEdit()
            self.edit_dt.setFixedWidth(80)
            self.edit_dt.setFont(QFont('Times', 14, QFont.Bold))
            self.edit_dt.setText(str(Sampling_Timer))
            self.lbl_edit_dt = QLabel('sampling dt[ms] : ')
            self.lbl_edit_dt.setFont(QFont('Times', 14))
            
            self.edit_dt.returnPressed.connect(self.edit_dt_changed)
            #self.edit_dt.editingFinished.connect(self.edit_dt_changed)
            
            Splitter_Display.addWidget(Button)
                
            ButtonLayout.addWidget(self.btn_Start)
            ButtonLayout.addWidget(self.btn_Pause) 
            ButtonLayout.addWidget(self.btn_Exit)
            ButtonLayout.setSpacing(20)
            self.btn_Start.clicked.connect(self.btn_Start_click)       
            self.btn_Exit.clicked.connect(self.btn_Exit_click)   
            self.btn_Pause.clicked.connect(self.btn_Pause_click)
            #ButtonLayout.addStretch(1)
            ButtonLayout.addWidget(self.lbl_file_name, Qt.AlignRight)
            ButtonLayout.addWidget(self.file_name, Qt.AlignLeft)
            #ButtonLayout.addStretch(1)
            ButtonLayout.addWidget(self.lbl_1_current_time, Qt.AlignRight)
            ButtonLayout.addWidget(self.lbl_2_current_time, Qt.AlignLeft)
            #ButtonLayout.addStretch(1)
            ButtonLayout.addWidget(self.lbl_1_start_sampling_time, Qt.AlignRight)
            ButtonLayout.addWidget(self.lbl_2_start_sampling_time, Qt.AlignLeft)  
            #ButtonLayout.addStretch(1)
            ButtonLayout.addWidget(self.lbl_edit_dt, Qt.AlignRight)
            ButtonLayout.addWidget(self.edit_dt, Qt.AlignLeft)
            
            self.spacer = QSpacerItem(20,20)
            
            self.x_min = list(range(Nb_of_PlotWindows)) #scale x-axis
            self.x_max = list(range(Nb_of_PlotWindows))
            self.y_min = list(range(Nb_of_PlotWindows)) #scale y-axis
            self.y_max = list(range(Nb_of_PlotWindows))   
            self.lbl_x_edit = list(range(Nb_of_PlotWindows))
            self.lbl_y_edit = list(range(Nb_of_PlotWindows))
            self.edit_x_min = list(range(Nb_of_PlotWindows)) 
            self.edit_x_max = list(range(Nb_of_PlotWindows))  
            self.edit_y_min = list(range(Nb_of_PlotWindows)) 
            self.edit_y_max = list(range(Nb_of_PlotWindows))              
            self.sensor_value = list(range(Nb_all_sensors)) # actual sampled value
            self.lbl_sensor_name = list(range(Nb_all_sensors))
            self.ch_AutoScale_x = list(range(Nb_of_PlotWindows))
            self.ch_AutoScale_y = list(range(Nb_of_PlotWindows))
            self.ch_sensor_value = list(range(Nb_all_sensors))
            self.edit_Pyro_em = list(range(Nb_of_Pyrometer))
            self.edit_Pyro_tr = list(range(Nb_of_Pyrometer))
            self.lbl_edit_Pyro_em = list(range(Nb_of_Pyrometer))
            self.lbl_edit_Pyro_tr = list(range(Nb_of_Pyrometer))
            self.lbl_Pyro_model = list(range(Nb_of_Pyrometer))
            self.Pyro_model = list(range(Nb_of_Pyrometer))
            self.lbl_Pyro_Distance = list(range(Nb_of_Pyrometer))
            self.Pyro_Distance = list(range(Nb_of_Pyrometer))
            self.ch_Pilot = list(range(Nb_of_Pyrometer))
            self.lbl_Pyro_t90 = list(range(Nb_of_Pyrometer))
            self.edit_Pyro_t90 = list(range(Nb_of_Pyrometer))
            self.edit_Pyro_array_em = list(range(Nb_of_pyro_array_heads))
            self.lbl_edit_Pyro_array_em = list(range(Nb_of_pyro_array_heads))
            self.lbl_Pyro_array_model = list(range(Nb_of_pyro_array_heads))
            self.Pyro_array_model = list (range(Nb_of_pyro_array_heads))   
            self.lbl_Pyro_array_t90 = list(range(Nb_of_pyro_array_heads))
            self.edit_Pyro_array_t90 = list(range(Nb_of_pyro_array_heads))            
            self.ch_LSYNC = list(range(Nb_of_DAQ_sensor_types))
            self.ch_OCOM = list(range(Nb_of_DAQ_sensor_types))
            self.ch_AZER = list(range(Nb_of_DAQ_sensor_types))
            self.filter_state = list(range(Nb_of_DAQ_sensor_types))
            self.filter_count = list(range(Nb_of_DAQ_sensor_types))
            self.lbl_filter_state = list(range(Nb_of_DAQ_sensor_types))
            self.lbl_filter_count = list(range(Nb_of_DAQ_sensor_types))
            self.lbl_nplc = list(range(Nb_of_DAQ_sensors))
            self.nplc = list(range(Nb_of_DAQ_sensors))
            
            for i in range(Nb_of_DAQ_sensor_types):
                self.ch_LSYNC[i] = QCheckBox('LSYNC ' + daq_sensor_types[i])
                if DAQ_lsync:
                    self.ch_LSYNC[i].setChecked(True)
                else:
                    self.ch_LSYNC[i].setChecked(False)
                self.ch_LSYNC[i].setFont(QFont('Times', 12))
                
                self.ch_OCOM[i] = QCheckBox('OCOM ' + daq_sensor_types[i])
                if DAQ_ocom:
                    self.ch_OCOM[i].setChecked(True)
                else:
                    self.ch_OCOM[i].setChecked(False)
                self.ch_OCOM[i].setFont(QFont('Times', 12)) 
                
                self.ch_AZER[i] = QCheckBox('AZER ' + daq_sensor_types[i])
                if DAQ_azer:
                    self.ch_AZER[i].setChecked(True)
                else:
                    self.ch_AZER[i].setChecked(False)
                self.ch_AZER[i].setFont(QFont('Times', 12))                                

                self.lbl_filter_state[i] = QLabel('Filter ' + daq_sensor_types[i], alignment=Qt.AlignRight)
                self.lbl_filter_state[i].setFont(QFont('Times', 12))
                self.filter_state[i] = QComboBox()
                self.filter_state[i].setFont(QFont('Times', 12))
                self.filter_state[i].addItem('OFF')
                self.filter_state[i].addItem('repeat')
                #self.filter_state[i].addItem('moving')
                self.lbl_filter_count[i] = QLabel('Counts ' + daq_sensor_types[i], alignment=Qt.AlignRight)
                self.lbl_filter_count[i].setFont(QFont('Times', 12))
                self.filter_count[i] = LineEdit()
                self.filter_count[i].setFixedWidth(80)
                self.filter_count[i].setFont(QFont('Times', 12))
                self.filter_count[i].setEnabled(False)
               
            for i in range(Nb_of_DAQ_sensors):
                self.lbl_nplc[i] = QLabel('NPLC :', alignment=Qt.AlignRight)
                self.lbl_nplc[i].setFont(QFont('Times', 12)) 
                self.nplc[i] = LineEdit()
                self.nplc[i].setFixedWidth(80)
                self.nplc[i].setFont(QFont('Times', 12))
                self.nplc[i].setText(str(daq_nplc_list[i]))
                
            for i in range(Nb_of_pyro_array_heads):
                self.edit_Pyro_array_em[i] = QComboBox()
                self.edit_Pyro_array_em[i].setFont(QFont('Times', 14, QFont.Bold))
                self.edit_Pyro_array_em[i].setFixedWidth(80)                
                for j in range(10,101):
                    self.edit_Pyro_array_em[i].addItem(str(j))        
                idx = self.edit_Pyro_array_em[i].findText(pyro_array_em_list[i])
                self.edit_Pyro_array_em[i].setCurrentIndex(idx)  
                self.lbl_Pyro_array_t90[i] = QLabel('t90 [s] : ')
                self.lbl_Pyro_array_t90[i].setFont(QFont('Times', 12))  
                self.lbl_Pyro_array_t90[i].setAlignment(Qt.AlignRight)
                self.edit_Pyro_array_t90[i] = QComboBox()
                self.edit_Pyro_array_t90[i].setFont(QFont('Times', 14))  
                self.edit_Pyro_array_t90[i].setFixedWidth(80)      
                s = str(pyro_array_t90_times[i]).replace('[','').replace(']','').replace(',','').replace("'",'').split()
                for j in range(len(s)):
                    self.edit_Pyro_array_t90[i].addItem(str(s[j]))
                self.edit_Pyro_array_t90[i].setCurrentIndex(int(pyro_array_t90_list[i])-1)    
                
                self.lbl_edit_Pyro_array_em[i] = QLabel('Emission [%]: ')
                self.lbl_edit_Pyro_array_em[i].setFont(QFont('Times', 12))  
                self.lbl_edit_Pyro_array_em[i].setAlignment(Qt.AlignRight)
                self.lbl_Pyro_array_model[i] = QLabel('Head ' + str(i+1) + ' :')
                self.lbl_Pyro_array_model[i].setFont(QFont('Times', 12))   
                self.lbl_Pyro_array_model[i].setAlignment(Qt.AlignRight)                                
                self.Pyro_array_model[i] = QLabel(pyro_array_model_list[i])
                self.Pyro_array_model[i].setFont(QFont('Times', 12))   
                self.Pyro_array_model[i].setAlignment(Qt.AlignRight)                  
                
            for i in range(Nb_of_Pyrometer):
                self.ch_Pilot[i] = QCheckBox('Pilot')
                self.ch_Pilot[i].setChecked(False)
                self.ch_Pilot[i].setFont(QFont('Times', 12))   
                
                self.edit_Pyro_em[i] = QComboBox()
                self.edit_Pyro_em[i].setFont(QFont('Times', 14, QFont.Bold))
                self.edit_Pyro_em[i].setFixedWidth(80)
                for j in range(10,101):
                    self.edit_Pyro_em[i].addItem(str(j))
                idx = self.edit_Pyro_em[i].findText(pyro_em_list[i])
                self.edit_Pyro_em[i].setCurrentIndex(idx)
                    
                self.edit_Pyro_tr[i] = QComboBox()
                self.edit_Pyro_tr[i].setFont(QFont('Times', 14, QFont.Bold))
                self.edit_Pyro_tr[i].setFixedWidth(80)
                for j in range(10,101):
                    self.edit_Pyro_tr[i].addItem(str(j))
                idx = self.edit_Pyro_tr[i].findText(pyro_tr_list[i])
                self.edit_Pyro_tr[i].setCurrentIndex(idx)    
                
                self.lbl_Pyro_t90[i] = QLabel('t90 [s] : ')
                self.lbl_Pyro_t90[i].setFont(QFont('Times', 12))  
                self.lbl_Pyro_t90[i].setAlignment(Qt.AlignRight)
                
                self.edit_Pyro_t90[i] = QComboBox()
                self.edit_Pyro_t90[i].setFont(QFont('Times', 14))  
                self.edit_Pyro_t90[i].setFixedWidth(80)
                
                s = str(pyro_t90_times[i]).replace('[','').replace(']','').replace(',','').replace("'",'').split()
                #print (len(s), int(pyro_t90_list[i])-1)
                for j in range(len(s)):
                    self.edit_Pyro_t90[i].addItem(str(s[j]))
                self.edit_Pyro_t90[i].setCurrentIndex(int(pyro_t90_list[i])-1)
                
                self.lbl_edit_Pyro_em[i] = QLabel('Emission [%]: ')
                self.lbl_edit_Pyro_em[i].setFont(QFont('Times', 12))  
                self.lbl_edit_Pyro_em[i].setAlignment(Qt.AlignRight)
                self.lbl_edit_Pyro_tr[i] = QLabel('Transmission [%] :', alignment=Qt.AlignRight)
                self.lbl_edit_Pyro_tr[i].setFont(QFont('Times', 12))   
                #self.lbl_edit_Pyro_tr[i].setAlignment(Qt.AlignRight)                
                self.lbl_Pyro_model[i] = QLabel('Model :')
                self.lbl_Pyro_model[i].setFont(QFont('Times', 12))   
                self.lbl_Pyro_model[i].setAlignment(Qt.AlignRight)                                
                self.Pyro_model[i] = QLabel(pyro_model_list[i])
                self.Pyro_model[i].setFont(QFont('Times', 12))   
                self.Pyro_model[i].setAlignment(Qt.AlignRight)
                self.lbl_Pyro_Distance[i] = QLabel('Distance :')
                self.lbl_Pyro_Distance[i].setFont(QFont('Times', 12))   
                self.Pyro_Distance[i] = QLabel(pyro_distance_list[i])
                self.Pyro_Distance[i].setFont(QFont('Times', 12))                
            
            for i in range(Nb_of_PlotWindows):
                self.lbl_x_edit[i] = QLabel('Time [s] : ')
                self.lbl_x_edit[i].setFont(QFont('Times', 12))
                self.lbl_x_edit[i].setAlignment(Qt.AlignRight)
                self.lbl_y_edit[i] = QLabel('Temp [°C] : ')
                idx = gr_idx.index(i)
                if sensor_list[idx] == 'Rogowski':
                    self.lbl_y_edit[i] = QLabel('Current [A] : ')
                if sensor_list[idx] == 'DCV-100mV':
                    self.lbl_y_edit[i] = QLabel('Voltage [mV] : ')
                if sensor_list[idx] == 'DCV':
                    self.lbl_y_edit[i] = QLabel('Voltage [V] : ')
                self.lbl_y_edit[i].setFont(QFont('Times', 12))  
                self.lbl_y_edit[i].setAlignment(Qt.AlignRight)
                
                self.edit_x_min[i] = LineEdit()
                self.edit_x_min[i].setFixedWidth(90)
                self.edit_x_min[i].setFont(QFont('Times', 14, QFont.Bold))
                self.x_min[i]=x_min
                self.edit_x_min[i].setText(str("%4.0f" % self.x_min[i]))
                self.edit_x_min[i].setEnabled(False)
                
                self.edit_x_max[i] = LineEdit()
                self.edit_x_max[i].setFixedWidth(90)
                self.edit_x_max[i].setFont(QFont('Times', 14, QFont.Bold))
                self.x_max[i]=x_max
                self.edit_x_max[i].setText(str("%4.0f" % self.x_max[i]))
                self.edit_x_max[i].setEnabled(False)
                
                self.edit_y_min[i] = LineEdit()
                self.edit_y_min[i].setFixedWidth(90)
                self.edit_y_min[i].setFont(QFont('Times', 14, QFont.Bold))
                self.y_min[i]=y_min
                self.edit_y_min[i].setText(str("%4.3f" % self.y_min[i]))
                self.edit_y_min[i].setEnabled(False)
 
                self.edit_y_max[i] = LineEdit()
                self.edit_y_max[i].setFixedWidth(90)
                self.edit_y_max[i].setFont(QFont('Times', 14, QFont.Bold))
                self.y_max[i]=y_max
                self.edit_y_max[i].setText(str("%4.3f" % self.y_max[i]))
                self.edit_y_max[i].setEnabled(False)   
                
                self.ch_AutoScale_x[i] = QCheckBox('Autoscale X')
                self.ch_AutoScale_x[i].setChecked(True)
                self.gr[i].enableAutoRange(axis='x')
                self.ch_AutoScale_x[i].setFont(QFont('Times', 12))    
                self.ch_AutoScale_x[i].setEnabled(True)
                
                self.ch_AutoScale_y[i] = QCheckBox('Autoscale Y')
                self.ch_AutoScale_y[i].setChecked(True)
                self.gr[i].enableAutoRange(axis='y')
                self.ch_AutoScale_y[i].setFont(QFont('Times', 12))    
                self.ch_AutoScale_y[i].setEnabled(True)
                
            z_p = 0
            row_idx = [0 for i in range(Nb_of_PlotWindows)]
            col_idx = [0 for i in range(Nb_of_PlotWindows)]
            
            for i in range(Nb_of_PlotWindows):
                
                row_idx[i] = 6 # for the channels later on
                idx = gr_idx.index(i)
                if sensor_list[idx] == 'Arduino':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i], 0, 3, 1, 3) 
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i], 1, 3, 1, 3)
                if sensor_list[idx] == 'Pyro':
                    ParameterGroupLayout[i].addWidget(self.lbl_Pyro_model[z_p], 0, 0)
                    ParameterGroupLayout[i].setAlignment(self.lbl_Pyro_model[z_p], Qt.AlignBottom|Qt.AlignLeft)
                    ParameterGroupLayout[i].addWidget(self.Pyro_model[z_p], 0, 1)       
                    ParameterGroupLayout[i].setAlignment(self.Pyro_model[z_p], Qt.AlignBottom|Qt.AlignLeft)
                    ParameterGroupLayout[i].addWidget(self.lbl_Pyro_Distance[z_p], 0, 2)
                    ParameterGroupLayout[i].setAlignment(self.lbl_Pyro_Distance[z_p], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.Pyro_Distance[z_p], 0, 3)
                    ParameterGroupLayout[i].setAlignment(self.Pyro_Distance[z_p], Qt.AlignBottom)                    
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignLeft)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 1, 2, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 2, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_y_edit[i], Qt.AlignLeft)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 2, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 2, 2, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i], 1, 3, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i], 2, 3, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.lbl_edit_Pyro_em[z_p], 3, 0)
                    ParameterGroupLayout[i].setAlignment(self.lbl_edit_Pyro_em[z_p], Qt.AlignLeft)
                    ParameterGroupLayout[i].addWidget(self.edit_Pyro_em[z_p], 3, 1)
                    ParameterGroupLayout[i].addWidget(self.lbl_edit_Pyro_tr[z_p], 3, 2)
                    ParameterGroupLayout[i].addWidget(self.edit_Pyro_tr[z_p], 3, 3)
                    ParameterGroupLayout[i].addWidget(self.lbl_Pyro_t90[z_p], 4, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_Pyro_t90[z_p], Qt.AlignLeft)
                    ParameterGroupLayout[i].addWidget(self.edit_Pyro_t90[z_p], 4, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.ch_Pilot[z_p], 4, 2, 1, 1)
                    ParameterGroupLayout[i].addWidget(QHLine(), 5, 0, 1, 4)
                    row_idx[i] = 6
                    z_p += 1
                if sensor_list[idx] == 'Pyro_head':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)                    
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i],0,3,1,3)
                    ParameterGroupLayout[i].setAlignment(self.ch_AutoScale_x[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i],1,3,1,3)
                    for z in range(Nb_of_pyro_array_heads):
                        ParameterGroupLayout[i].addWidget(self.lbl_Pyro_array_model[z], 2+z*2, 0, 1, 1)
                        ParameterGroupLayout[i].setAlignment(self.lbl_Pyro_array_model[z], Qt.AlignLeft|Qt.AlignBottom)
                        self.lbl_Pyro_array_model[z].setStyleSheet('color: %s'%self.mycolors[color_list[idx+z]])
                        ParameterGroupLayout[i].addWidget(self.Pyro_array_model[z], 2+z*2, 1, 1, 1)
                        ParameterGroupLayout[i].setAlignment(self.Pyro_array_model[z], Qt.AlignLeft|Qt.AlignBottom)
                        self.Pyro_array_model[z].setStyleSheet('color: %s'%self.mycolors[color_list[idx+z]])
                        ParameterGroupLayout[i].addWidget(self.lbl_edit_Pyro_array_em[z], 3+z*2, 0, 1, 1)
                        ParameterGroupLayout[i].addWidget(self.edit_Pyro_array_em[z], 3+z*2, 1, 1, 1)
                        ParameterGroupLayout[i].addWidget(self.lbl_Pyro_array_t90[z], 3+z*2, 2, 1, 1)
                        ParameterGroupLayout[i].addWidget(self.edit_Pyro_array_t90[z], 3+z*2, 3, 1, 1)
                    row_idx[i] = 2 + 2 * Nb_of_pyro_array_heads
                    ParameterGroupLayout[i].addWidget(QHLine(),row_idx[i], 0, 1, 4)
                    row_idx[i] = 2 + 2 * Nb_of_pyro_array_heads + 1
                    
                if sensor_list[idx] == 'TE':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)                    
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i],0,3,1,3)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i],1,3,1,3)
                    i_TE = daq_sensor_types.index('TE')
                    ParameterGroupLayout[i].addWidget(self.ch_LSYNC[i_TE],2,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.ch_OCOM[i_TE],2,1,1,1)
                    ParameterGroupLayout[i].addWidget(self.ch_AZER[i_TE],2,2,1,1)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_state[i_TE],3,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.filter_state[i_TE],3,1,1,1)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_count[i_TE],3,2,1,1, Qt.AlignRight)
                    ParameterGroupLayout[i].addWidget(self.filter_count[i_TE],3,3,1,1)
                if sensor_list[idx] == 'PT':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)                    
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i],0,3,1,3)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i],1,3,1,3)
                    if '100' in range_list:
                        i_PT = daq_sensor_types.index('PT-100')
                        ParameterGroupLayout[i].addWidget(self.ch_LSYNC[i_PT],2,0,1,1)
                        ParameterGroupLayout[i].addWidget(self.ch_OCOM[i_PT],2,1,1,2)
                        ParameterGroupLayout[i].addWidget(self.ch_AZER[i_PT],2,3,1,1)
                        ParameterGroupLayout[i].addWidget(self.lbl_filter_state[i_PT],3,0,1,1)
                        ParameterGroupLayout[i].addWidget(self.filter_state[i_PT],3,1,1,1)                    
                        ParameterGroupLayout[i].addWidget(self.lbl_filter_count[i_PT],3,2,1,1, Qt.AlignRight)
                        ParameterGroupLayout[i].addWidget(self.filter_count[i_PT],3,3,1,1)
                    if '1000' in range_list:
                        i_PT = daq_sensor_types.index('PT-1000')
                        ParameterGroupLayout[i].addWidget(self.ch_LSYNC[i_PT],4,0,1,1)
                        ParameterGroupLayout[i].addWidget(self.ch_OCOM[i_PT],4,1,1,2)
                        ParameterGroupLayout[i].addWidget(self.ch_AZER[i_PT],4,3,1,1)
                        ParameterGroupLayout[i].addWidget(self.lbl_filter_state[i_PT],5,0,1,1)
                        ParameterGroupLayout[i].addWidget(self.filter_state[i_PT],5,1,1,1)                    
                        ParameterGroupLayout[i].addWidget(self.lbl_filter_count[i_PT],5,2,1,1, Qt.AlignRight)
                        ParameterGroupLayout[i].addWidget(self.filter_count[i_PT],5,3,1,1)                    
                        row_idx[i] = 6
                if sensor_list[idx] == 'Rogowski':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)                    
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i],0,3,1,3)
                    ParameterGroupLayout[i].setAlignment(self.ch_AutoScale_x[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i],1,3,1,3)
                    i_Rogowski = daq_sensor_types.index('Rogowski')
                    ParameterGroupLayout[i].addWidget(self.ch_LSYNC[i_Rogowski],2,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.ch_AZER[i_Rogowski],2,1,1,2)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_state[i_Rogowski],3,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.filter_state[i_Rogowski],3,1,1,1)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_count[i_Rogowski],3,2,1,1, Qt.AlignRight)
                    ParameterGroupLayout[i].addWidget(self.filter_count[i_Rogowski],3,3,1,1) 
                    ParameterGroupLayout[i].addWidget(QHLine(), 4, 0, 1, 4)
                    row_idx[i] = 5
                if sensor_list[idx] == 'DCV':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)                    
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i],0,3,1,3)
                    ParameterGroupLayout[i].setAlignment(self.ch_AutoScale_x[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i],1,3,1,3)                    
                    i_DCV = daq_sensor_types.index('DCV')
                    ParameterGroupLayout[i].addWidget(self.ch_LSYNC[i_DCV],2,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.ch_AZER[i_DCV],2,1,1,2)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_state[i_DCV],3,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.filter_state[i_DCV],3,1,1,1)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_count[i_DCV],3,2,1,1, Qt.AlignRight)
                    ParameterGroupLayout[i].addWidget(self.filter_count[i_DCV],3,3,1,1) 
                if sensor_list[idx] == 'DCV-100mV':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)                    
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i],0,3,1,3)
                    ParameterGroupLayout[i].setAlignment(self.ch_AutoScale_x[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i],1,3,1,3)
                    i_DCV_100mV = daq_sensor_types.index('DCV-100mV')
                    ParameterGroupLayout[i].addWidget(self.ch_LSYNC[i_DCV_100mV],2,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.ch_AZER[i_DCV_100mV],2,1,1,2)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_state[i_DCV_100mV],3,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.filter_state[i_DCV_100mV],3,1,1,1)                    
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_count[i_DCV_100mV],3,2,1,1, Qt.AlignRight)
                    ParameterGroupLayout[i].addWidget(self.filter_count[i_DCV_100mV],3,3,1,1)
                    ParameterGroupLayout[i].addWidget(QHLine(), 4, 0, 1, 4)
                    row_idx[i] = 5                    
                if sensor_list[idx] == 'ACV':
                    ParameterGroupLayout[i].addWidget(self.lbl_x_edit[i], 0, 0, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.lbl_x_edit[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_min[i], 0, 1, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_min[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.edit_x_max[i], 0, 2, 1, 1)
                    ParameterGroupLayout[i].setAlignment(self.edit_x_max[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.lbl_y_edit[i], 1, 0, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_min[i], 1, 1, 1, 1)
                    ParameterGroupLayout[i].addWidget(self.edit_y_max[i], 1, 2, 1, 1)                    
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_x[i],0,3,1,3)
                    ParameterGroupLayout[i].setAlignment(self.ch_AutoScale_x[i], Qt.AlignBottom)
                    ParameterGroupLayout[i].addWidget(self.ch_AutoScale_y[i],1,3,1,3)                    
                    i_ACV = daq_sensor_types.index('ACV')
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_state[i_ACV],3,0,1,1)
                    ParameterGroupLayout[i].addWidget(self.filter_state[i_ACV],3,1,1,1)
                    ParameterGroupLayout[i].addWidget(self.lbl_filter_count[i_ACV],3,2,1,1, Qt.AlignRight)
                    ParameterGroupLayout[i].addWidget(self.filter_count[i_ACV],3,3,1,1)                
                
            for i in range(Nb_all_sensors):
                #self.lbl_sensor_name[i] = QLabel('C.' + str(ch_list[i]))
                self.lbl_sensor_name[i] = QLabel(alias_list[i])
                self.lbl_sensor_name[i].setFont(QFont('Times', 12, QFont.Bold))
                self.lbl_sensor_name[i].setStyleSheet('color: %s'%self.mycolors[color_list[i]])        
                self.sensor_value[i] = QLabel('xxx.xxx')
                self.sensor_value[i].setFont(QFont('Times', 14, QFont.Bold))
                self.sensor_value[i].setStyleSheet('color: %s' %self.mycolors[color_list[i]])
                self.ch_sensor_value[i] = QCheckBox('Hide')
                self.ch_sensor_value[i].setChecked(False)
                self.ch_sensor_value[i].setFont(QFont('Times', 12))
                
                ParameterGroupLayout[gr_idx[i]].addWidget(self.lbl_sensor_name[i], row_idx[gr_idx[i]], 0)
                ParameterGroupLayout[gr_idx[i]].addWidget(self.sensor_value[i], row_idx[gr_idx[i]], 1)
                ParameterGroupLayout[gr_idx[i]].addWidget(self.ch_sensor_value[i], row_idx[gr_idx[i]], 2)
                
                if i < Nb_of_DAQ_sensors:
                    ParameterGroupLayout[gr_idx[i]].addWidget(self.lbl_nplc[i], row_idx[gr_idx[i]], 3, Qt.AlignRight)
                    ParameterGroupLayout[gr_idx[i]].addWidget(self.nplc[i], row_idx[gr_idx[i]], 4)
                    
                row_idx[gr_idx[i]] += 1
                
             
            for i in range(Nb_of_PlotWindows):   
                self.ch_AutoScale_x[i].clicked.connect(partial(self.update_AutoScale_x, i))
                self.ch_AutoScale_y[i].clicked.connect(partial(self.update_AutoScale_y, i))
                self.edit_x_min[i].editingFinished.connect(partial(self.edit_x_min_changed, i))
                self.edit_x_max[i].editingFinished.connect(partial(self.edit_x_max_changed, i))                
                self.edit_y_min[i].editingFinished.connect(partial(self.edit_y_min_changed, i))
                self.edit_y_max[i].editingFinished.connect(partial(self.edit_y_max_changed, i))
            
            for i in range(Nb_of_DAQ_sensor_types):
                self.ch_LSYNC[i].clicked.connect(partial(self.update_LSYNC, i))
                self.ch_OCOM[i].clicked.connect(partial(self.update_OCOM, i))
                self.ch_AZER[i].clicked.connect(partial(self.update_AZER, i))
                self.filter_state[i].currentIndexChanged.connect(partial(self.update_filter_state, i))
                self.filter_count[i].returnPressed.connect(partial(self.update_filter_count, i))
            
            for i in range(Nb_of_DAQ_sensors):
                self.nplc[i].returnPressed.connect(partial(self.update_nplc, i))
                #self.nplc[i].editingFinished.connect(partial(self.update_nplc, i))
                
            for i in range(Nb_all_sensors):
                self.ch_sensor_value[i].clicked.connect(partial(self.update_HideSensor, i))
                
            for i in range (Nb_of_Pyrometer):
                self.ch_Pilot[i].clicked.connect(partial(self.update_pilot, i))
                self.edit_Pyro_em[i].currentIndexChanged.connect(partial(self.edit_Pyro_em_changed, i))
                self.edit_Pyro_tr[i].currentIndexChanged.connect(partial(self.edit_Pyro_tr_changed, i))   
                self.edit_Pyro_t90[i].currentIndexChanged.connect(partial(self.edit_Pyro_t90_changed, i))
                
            for i in range (Nb_of_pyro_array_heads):
                self.edit_Pyro_array_em[i].currentIndexChanged.connect(partial(self.edit_Pyro_array_em_changed, i))
                self.edit_Pyro_array_t90[i].currentIndexChanged.connect(partial(self.edit_Pyro_array_t90_changed, i))            
                
        def edit_Pyro_array_t90_changed(self, u):
            pyro_array_t90_time[u] = self.edit_Pyro_array_t90[u].currentText()
            print (pyro_array_t90_time, pyro_array_t90_time[u])
            idx = self.edit_Pyro_array_t90[u].currentIndex()
            Pyrometer_Array.Write_Pyro_Array_Para(u, 't90', str(idx))
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            ProtocolFile.write(time_abs + ': Sensor ' + pyro_array_alias_list[u] + ', t90[s]=' + str(pyro_array_t90_time[u]) + '\n')
            ProtocolFile.close()            
        
        def edit_Pyro_t90_changed(self, u):
            pyro_t90_time[u] = self.edit_Pyro_t90[u].currentText()
            print (pyro_t90_time, pyro_t90_time[u])
            idx = self.edit_Pyro_t90[u].currentIndex()
            Pyrometer.Write_Pyro_Para(u, 't90', str(idx))
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            ProtocolFile.write(time_abs + ': Sensor ' + pyro_alias_list[u] + ', t90[s]=' + str(pyro_t90_time[u]) + '\n')
            ProtocolFile.close()             
        
        def edit_Pyro_array_em_changed(self, u):
            pyro_array_em_list[u] = self.edit_Pyro_array_em[u].currentText()
            Pyrometer_Array.Write_Pyro_Array_Para(u, 'e', pyro_array_em_list[u]) 
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            ProtocolFile.write(time_abs + ': Sensor ' + pyro_array_alias_list[u] + ', emission=' + str(pyro_array_em_list[u]) + '%\n')
            ProtocolFile.close()             
        
        def edit_Pyro_em_changed(self, u):
            pyro_em_list[u] = self.edit_Pyro_em[u].currentText()
            Pyrometer.Write_Pyro_Para(u, 'e', pyro_em_list[u])
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            ProtocolFile.write(time_abs + ': Sensor ' + pyro_alias_list[u] + ', emission=' + str(pyro_em_list[u]) + '%\n')
            ProtocolFile.close()               
                
        def edit_Pyro_tr_changed(self, u):
            pyro_tr_list[u] = self.edit_Pyro_tr[u].currentText()
            Pyrometer.Write_Pyro_Para(u, 't', pyro_tr_list[u]) 
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            ProtocolFile.write(time_abs + ': Sensor ' + pyro_alias_list[u] + ', transmission=' + str(pyro_tr_list[u]) + '%\n')
            ProtocolFile.close()            
                
        def update_pilot(self, u):
            Pyrometer.Write_Pilot(u, self.ch_Pilot[u].isChecked())      

        def update_filter_count(self, u):
            val_str = self.filter_count[u].text()
            val = int(val_str)
            self.filter_count[u].clearFocus()
            DAQ_6510.Write_Filter_Count(u, val) 
            
        def update_filter_state(self, u):
            val_str = self.filter_state[u].currentText()
            if val_str == 'OFF':
                self.filter_count[u].setEnabled(False)
            else:
                self.filter_count[u].setEnabled(True)
                self.filter_count[u].setText('5')                
            DAQ_6510.Write_Filter_State(u, val_str)
        
        def update_nplc(self, u):
            val_str = self.nplc[u].text().replace(',', '.')
            val = float(val_str)
            self.nplc[u].clearFocus()
            #self.nplc[u].deselect()
            self.nplc[u].setStyleSheet('color: black')            
            DAQ_6510.Write_NPLC(u, val)
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            ProtocolFile.write(time_abs + ': Sensor ' + daq_alias_list[u] + ', nplc=' + str(val) + '\n')
            ProtocolFile.close()
        
        def update_LSYNC(self, u):
            #if daq_sensor_types[u] == 'TE':
                #DAQ_6510.Write_LSYNC(u, self.ch_LSYNC[u].isChecked())
            #if daq_sensor_types[u] == 'PT-100':
                #DAQ_6510.Write_LSYNC(u, self.ch_LSYNC[u].isChecked())
            #if daq_sensor_types[u] == 'PT-1000':
                #DAQ_6510.Write_LSYNC(u, self.ch_LSYNC[u].isChecked())
            #if daq_sensor_types[u] == 'DCV-100mV' or daq_sensor_types[u] == 'DCV':
                #DAQ_6510.Write_LSYNC(u, self.ch_LSYNC[u].isChecked())           
            #if daq_sensor_types[u] == 'Rogowski':
                #DAQ_6510.Write_LSYNC(u, self.ch_LSYNC[u].isChecked())                           
            DAQ_6510.Write_LSYNC(u, self.ch_LSYNC[u].isChecked())
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            val = self.ch_LSYNC[u].isChecked()
            #ProtocolFile.write(time_abs + ': Sensor ' + daq_alias_list[u] + ', LSYNC=' + str(val) + '\n')
            ProtocolFile.write(time_abs + ': Sensor type ' + daq_sensor_types[u] + ', LSYNC=' + str(val) + '\n')
            ProtocolFile.close()
            
        def update_OCOM(self, u):
            #if daq_sensor_types[u] == 'TE':
                #DAQ_6510.Write_OCOM(u, self.ch_OCOM[u].isChecked())
            #if daq_sensor_types[u] == 'PT-100':
                #DAQ_6510.Write_OCOM(u, self.ch_OCOM[u].isChecked())
            #if daq_sensor_types[u] == 'PT-1000':
                #DAQ_6510.Write_OCOM(u, self.ch_OCOM[u].isChecked())                    
            #if daq_sensor_types[u] == 'DCV-100mV' or daq_sensor_types[u] == 'DCV':
                #DAQ_6510.Write_OCOM(u, self.ch_OCOM[u].isChecked()) 
            #if daq_sensor_types[u] == 'Rogowski':
                #DAQ_6510.Write_OCOM(u, self.ch_OCOM[u].isChecked())
            DAQ_6510.Write_OCOM(u, self.ch_OCOM[u].isChecked())
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            val = self.ch_OCOM[u].isChecked()
            ProtocolFile.write(time_abs + ': Sensor type ' + daq_sensor_types[u] + ', OCOM=' + str(val) + '\n')
            ProtocolFile.close()
                
                
        def update_AZER(self, u):
            #if daq_sensor_types[u] == 'TE':
                #DAQ_6510.Write_AZER(u, self.ch_AZER[u].isChecked())
            #if daq_sensor_types[u] == 'PT-100':
                #DAQ_6510.Write_AZER(u, self.ch_AZER[u].isChecked())
            #if daq_sensor_types[u] == 'PT-1000':
                #DAQ_6510.Write_AZER(u, self.ch_AZER[u].isChecked())
            #if daq_sensor_types[u] == 'DCV-100mV' or daq_sensor_types[u] == 'DCV':
                #DAQ_6510.Write_AZER(u, self.ch_AZER[u].isChecked())     
            #if daq_sensor_types[u] == 'Rogowski':
                #DAQ_6510.Write_AZER(u, self.ch_AZER[u].isChecked())    
            DAQ_6510.Write_AZER(u, self.ch_AZER[u].isChecked())                
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            val = self.ch_AZER[u].isChecked()
            ProtocolFile.write(time_abs + ': Sensor type ' + daq_sensor_types[u] + ', AZER=' + str(val) + '\n')
            ProtocolFile.close()
                
        def calc_x_2_ticks(self, u):
            # calculate the datetime axis at the top x axis
            delta_t = int(self.x_max[u] - self.x_min[u])
            x2_min = time_start + datetime.timedelta(seconds=self.x_min[u])
            x2_max = (x2_min + datetime.timedelta(seconds=delta_t)).strftime('%H:%M:%S')
            x2_list = []
            x2_ticks = []
            for i in range(x2_Nb_ticks):
                x2_list.append((x2_min + datetime.timedelta(seconds=i*delta_t/(x2_Nb_ticks-1))).strftime('%H:%M:%S'))
                x2_ticks.append([self.x_min[u]+i*delta_t/(x2_Nb_ticks-1), x2_list[i]])            
                self.ax_X_2[u].setTicks([x2_ticks,[]])    
        
        def edit_x_min_changed(self, u):
            self.x_min[u] = float(self.edit_x_min[u].text().replace(',','.'))
            self.edit_x_min[u].setText(str("%4.0f" % self.x_min[u]))
            self.edit_x_min[u].setStyleSheet('color: black')
            self.edit_x_min[u].clearFocus()
            self.gr[u].setXRange(self.x_min[u], self.x_max[u], padding=self.pdg)
            self.calc_x_2_ticks(u)
        def edit_x_max_changed(self, u):
            self.x_max[u] = float(self.edit_x_max[u].text().replace(',','.'))
            self.edit_x_max[u].setText(str("%4.0f" % self.x_max[u]))
            self.edit_x_max[u].setStyleSheet('color: black')
            self.edit_x_max[u].clearFocus()
            self.gr[u].setXRange(self.x_min[u], self.x_max[u], padding=self.pdg)
            self.calc_x_2_ticks(u)
        def edit_y_min_changed(self, u):
            self.y_min[u] = float(self.edit_y_min[u].text().replace(',','.'))
            #self.edit_y_min[u].setText(str("%4.5f" % self.y_min[u]))
            idx = gr_idx.index(u)
            if sensor_list[idx] == 'DCV-100mV':
                self.edit_y_min[u].setText(str("%4.5f" % self.y_min[u]))
            elif sensor_list[idx] == 'DCV':
                self.edit_y_min[u].setText(str("%3.3f" % self.y_min[u]))
            else:
                self.edit_y_min[u].setText(str("%3.1f" % self.y_min[u]))
            self.edit_y_min[u].setStyleSheet('color: black')
            self.edit_y_min[u].clearFocus()
            self.gr[u].setYRange(self.y_min[u], self.y_max[u], padding=self.pdg)
        def edit_y_max_changed(self, u):
            self.y_max[u] = float(self.edit_y_max[u].text().replace(',','.'))
            #self.edit_y_max[u].setText(str("%4.5f" % self.y_max[u])) 
            idx = gr_idx.index(u)
            if sensor_list[idx] == 'DCV-100mV':
                self.edit_y_max[u].setText(str("%4.5f" % self.y_max[u]))
            elif sensor_list[idx] == 'DCV':
                self.edit_y_max[u].setText(str("%3.3f" % self.y_max[u]))
            else:
                self.edit_y_max[u].setText(str("%3.1f" % self.y_max[u]))
            self.edit_y_max[u].setStyleSheet('color: black')
            self.edit_y_max[u].clearFocus()
            self.gr[u].setYRange(self.y_min[u], self.y_max[u], padding=self.pdg)                   
        
        
        def edit_dt_changed(self):
            val = int(self.edit_dt.text())
            self.edit_dt.clearFocus()
            Sampling_Timer = val
            print ('Sampling intervall set to: ', Sampling_Timer, ' ms')
            self.timer.setInterval(Sampling_Timer)
            ProtocolFile = open(ProtocolFileName, 'a')
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            ProtocolFile.write(time_abs + ': sampling with ' +  str(Sampling_Timer) + ' [ms]\n')
            ProtocolFile.close()            
            
        
        def update_HideSensor(self, u):
            if self.ch_sensor_value[u].isChecked():
                print ('Hide sensor ', ch_list[u])
                self.myPen[u] = pg.mkPen(None)
                self.pData_line[u].setPen(self.myPen[u])
                self.lbl_sensor_name[u].setEnabled(False)
            else:
                print ('Sensor ', ch_list[u], ' visible')
                self.myPen[u] = pg.mkPen(color=matplotlib.colors.cnames[self.mycolors[color_list[u]]])
                self.pData_line[u].setPen(self.myPen[u])       
                self.lbl_sensor_name[u].setEnabled(True)
            
        def update_AutoScale_x(self, u):
            if self.ch_AutoScale_x[u].isChecked():
                self.edit_x_min[u].setEnabled(False)
                self.edit_x_max[u].setEnabled(False)
                self.gr[u].enableAutoRange(axis='x')
            else:
                self.edit_x_min[u].setEnabled(True)
                self.edit_x_max[u].setEnabled(True)
                self.gr[u].disableAutoRange(axis='x')
        
        def update_AutoScale_y(self, u):
            if self.ch_AutoScale_y[u].isChecked():
                self.edit_y_min[u].setEnabled(False)
                self.edit_y_max[u].setEnabled(False) 
                self.gr[u].enableAutoRange(axis='y')
            else:
                self.edit_y_min[u].setEnabled(True)
                self.edit_y_max[u].setEnabled(True)
                self.gr[u].disableAutoRange(axis='y')

       
        def btn_Start_click(self):
            Init_Output_File(ch_list)
            self.file_name.setText(FileOutName)
            self.lbl_2_start_sampling_time.setText(datetime.datetime.now().strftime('%H:%M:%S'))
            self.btn_Exit.setEnabled(True)
            self.btn_Pause.setEnabled(True)
            self.btn_Start.setEnabled(False)
            self.Start_Sampling()
            if not args.test:
                if DAQ_present:
                    DAQ_6510.message_daq_display()
        
        def btn_Exit_click(self):
            print ('End of script.')
            if not args.test:
                if DAQ_present:
                    DAQ_6510.reset_daq()
            sys.exit(0)  
            
        def btn_Pause_click(self):
            self.btn_Start.setEnabled(True)
            self.btn_Exit.setEnabled(True)
            self.btn_Pause.setEnabled(False)
            print ('Pause....')
            self.timer.stop()
            
            self.pData_time = np.zeros((0, 2)) # Dim-0 = time/abs, Dim-1=time/s
            self.pData_temp = np.empty((0, Nb_all_sensors)) # following Dim's are temperatures            
            
            
            x = self.pData_time[:,0].astype(np.float)
            for i in range(Nb_all_sensors):
                y = self.pData_temp[:,i].astype(np.float)
                self.pData_line[i].setData(x, y, connect='finite')            
            
            
        def update_graphics(self):
            # the main loop to update the graphics output
            self.lbl_2_current_time.setText(datetime.datetime.now().strftime('%H:%M:%S'))
            time_abs = datetime.datetime.now().strftime('%H:%M:%S')
            time_actual = datetime.datetime.now()
            global sampling_started, dt_0
            if sampling_started:
                # because first sampled time should be 0
                sampling_started = False
                dt_0 = (time_actual - time_start).total_seconds()
                #print ('dt_0= ',dt_0)
            # each sampled step is a new row
            # time and temperatures are column items in the new row     
            new_time = list(range(0))
            dt = (time_actual - time_start).total_seconds() - dt_0
            new_time.append((dt))
            new_time.append((time_abs))
            
            # get the actual sensor values from the active instrument(s)
            measurement_list = get_measurements()
            
            new_temp = measurement_list[0]
            new_temp_2 = list(range(Nb_all_sensors))
            new_temp_2[:] = new_temp[:] #because of 'call by reference' otherwise
            new_ohm = measurement_list[1] #only in PT_1000_mode 'R+T'
            if len(new_temp_2) == 0:
                print ('Keithley reading timing error, ignoring this sampling step.\n')
            else:
                for i in range(Nb_all_sensors):
                    new_temp_2[i] = new_temp_2[i] * float(factor_list[i]) + float(offset_list[i])
            
                # matrix pData is for plot
                # add each completed sampling step to the matrix as new row
    
                #if np.nan not in new_temp:
                self.pData_time = np.vstack(((self.pData_time), (new_time)))
                self.pData_temp = np.vstack(((self.pData_temp), (new_temp_2)))
                
                x = self.pData_time[:,0].astype(float)
                
                for i in range(Nb_all_sensors):
                    y = self.pData_temp[:,i].astype(float)
                
                    #PyQtGraph workaround for NaN from instrument 
                    con = np.isfinite(y) 
                    if len(y) >= 2 and y[-2:-1] != np.nan:
                        y_ok = y[-2:-1]
                        y[~con] = y_ok
                    
                    self.pData_line[i].setData(x, y, connect = np.logical_and(con, np.roll(con, -1)))
                    
                    if sensor_list[i] == 'DCV-100mV':
                        self.sensor_value[i].setText(str(format(new_temp_2[i], '.6f')))
                    else:
                        self.sensor_value[i].setText(str(format(new_temp_2[i], '.3f')))
                        
                    # check scaling in the graph
                    g_i = gr_idx[i]
                    self.ax_X[g_i] = self.gr[g_i].getAxis('bottom')
                    self.ax_X_2[g_i] = self.gr[g_i].getAxis('top')
                    self.ax_Y[g_i] = self.gr[g_i].getAxis('left')
                    if self.ch_AutoScale_x[g_i].isChecked():
                        self.x_min[g_i] = self.ax_X[g_i].range[0]
                        self.x_max[g_i] = self.ax_X[g_i].range[1]
                        self.edit_x_min[g_i].setText(str("%4.0f" % self.x_min[g_i]))
                        self.edit_x_max[g_i].setText(str("%4.0f" % self.x_max[g_i]))
                        self.calc_x_2_ticks(g_i)
                    if self.ch_AutoScale_y[g_i].isChecked():
                        self.y_min[g_i] = self.ax_Y[g_i].range[0]
                        self.y_max[g_i] = self.ax_Y[g_i].range[1]
                        if sensor_list[i] == 'DCV-100mV':
                            self.edit_y_min[g_i].setText(str("%3.5f" % self.y_min[g_i]))
                            self.edit_y_max[g_i].setText(str("%3.5f" % self.y_max[g_i]))
                        elif sensor_list[i] == "DCV":
                            self.edit_y_min[g_i].setText(str("%3.3f" % self.y_min[g_i]))
                            self.edit_y_max[g_i].setText(str("%3.3f" % self.y_max[g_i]))
                        else:
                            self.edit_y_min[g_i].setText(str("%4.1f" % self.y_min[g_i]))
                            self.edit_y_max[g_i].setText(str("%4.1f" % self.y_max[g_i]))                     

                    
                    
                # write (append) each sampling to the output file
                OutputFile = open(FileOutName, 'a') 
                OutputFile.write(str(time_abs))
                OutputFile.write(str(format(dt, '.3f')).rjust(12))
                z = 0
                for i in range(Nb_all_sensors):
                    if sensor_list[i] == 'DCV-100mV':
                        OutputFile.write(str(format(new_temp_2[i], '.6f')).rjust(14))
                    else:    
                        OutputFile.write(str(format(new_temp_2[i], '.3f')).rjust(14))
                    if sensor_list[i] == 'PT' and range_list[i] == '1000' and PT_1000_mode == 'R+T':
                        OutputFile.write(str(format(new_ohm[z], '.4f')).rjust(12))
                        z += 1
                    
                    
                OutputFile.write('\n')
                OutputFile.close()            
            
        def Start_Sampling(self):
            # START button pressed
            global time_start, sampling_started
            print ('Start sampling.')
            time_start = datetime.datetime.now()
            x2_min = time_start
            self.timer.start()
            sampling_started = True
            
            
    gr_app = QApplication(sys.argv)
    gr = grPanel()
    
    screen_width = gr_app.desktop().screenGeometry().width()
    screen_height = gr_app.desktop().screenGeometry().height()    
    if screen_width == 1280:
        gr.resize(1180,900)
        gr.move(10, 10)
    else:
        gr.resize(1400,1100)
        gr.move(400, 10)
    #gr.resize(700,500) 
    #gr.move(10,10)
    gr.show()

    if (sys.flags.interactive != 1) or not hasattr(QtCore, 'PYQT_VERSION'):
                QApplication.instance().exec_()

    return()    



# start the GUI
Graphics()


print ('Sampling done ... exit script...')



