import serial
import pyvisa
import numpy as np
import random

global ser_daq, debug_daq, test_daq, reading_str, nb_reading_values, ch_list, sensor_list, type_list, \
       daq_sensor_types, nplc
global ch_list_temp, ch_list_TC_K, ch_list_TC_J, ch_list_ohm, ch_list_PT_100, \
       ch_list_PT_1000, ch_list_DCV_Volt, ch_list_DCV_100mV

    
###########################################################################
def init_daq(com, rate, bits, stop, parity, dbg, test, time):
###########################################################################
### Init the interface 
    
    global ser_daq, debug_daq, test_daq, time_daq, nplc, interface
    
    debug_daq = dbg
    test_daq = test
    time_daq = time
    
    if com != 'LAN':
        interface = 'COM'
        portName = 'COM'+str(com)
        try:
            serial.Serial(port=portName)
        except serial.SerialException:
            print ('Port ' + portName + ' not present')
            if not test_daq:
                quit()
        
        if not test_daq:
            ser_daq = serial.Serial(
                port = portName,
                baudrate = int(rate),
                stopbits = int(stop),
                bytesize = int(bits),
                parity = parity,
                timeout = 2.0) #2.0
    else:
        interface = 'LAN'
        rm = pyvisa.ResourceManager()
        ser_daq = rm.open_resource('daq')



###########################################################################
def get_daq():
###########################################################################
### get the measurements from the active channels
    
    cm_list = list(range(0))
    cm_list.append('TRAC:CLE\n')
    cm_list.append('TRAC:POIN 100\n')
    cm_list.append('ROUT:SCAN:CRE ' + reading_str + '\n')
    cm_list.append('ROUT:SCAN:COUN:SCAN 1\n')
    cm_list.append('INIT\n')
    cm_list.append('*WAI\n')
    
    
    readings = '1,' + str(nb_reading_values) + ','
    
    if not time_daq:
        # reading returns a comma separated string: ch,value,ch,value,...
        cm_list.append('TRAC:DATA? '+ readings + '"defbuffer1", CHAN, READ\n')
    else:
        # reading returns a comma separated string: ch,tst,value,ch,tst,value,...
        cm_list.append('TRAC:DATA? '+ readings + '"defbuffer1", CHAN, REL, READ\n')
        
    
    if not test_daq:
        for i in range(len(cm_list)):
            if debug_daq:
                print ('writing to COM port: ', cm_list[i])
            if interface == 'LAN':
                ser_daq.write(cm_list[i])
            else:
                ser_daq.write(cm_list[i].encode())
        if interface == 'LAN':
            instrument = ser_daq.read()
        else:
            instrument = ser_daq.readline().decode()
            
        if debug_daq:
            print ('reading from COM : ' + str(instrument))        
    else:
        instrument = ''
        for i in range(nb_reading_values):
            val = random.uniform(20,22)
            instrument = instrument + ch_list[i] + ',' + str(val) + ','
    return (instrument[:-1])
    

###########################################################################
def config_daq(ch, alias, s, t, types, nplc, PT1000mode, lsync, ocom, azer, adel):
###########################################################################
### Configure the measurement channels
### ch . channel list
### s : sensor list
### t : type of each sensor or each range
### types : sensor types
### nplc : nplc for each channel    
    global reading_str, nb_reading_values, ch_list, alias_list, sensor_list, type_list, \
           daq_sensor_types, daq_nplc_list, PT_1000_mode, daq_lsync, daq_ocom, daq_azer, daq_adel
    global ch_list_temp, ch_list_TC_K, ch_list_TC_J, ch_list_ohm, ch_list_PT_100, \
           ch_list_PT_1000, ch_list_DCV_Volt, ch_list_DCV_100mV, ch_list_ACV
    
    ch_nb_TC = list(range(0))
    ch_nb_PT_100 = list(range(0))
    ch_nb_PT_1000 = list(range(0))
    ch_nb_DCV_Volt = list(range(0))
    ch_nb_DCV_100mV = list(range(0))
    ch_nb_ACV = list(range(0))
    ch_nb_Rogowski = list(range(0))
    nplc_TE = list(range(0))
    nplc_PT_100 = list(range(0))
    nplc_PT_1000 = list(range(0))
    nplc_DCV_Volt = list(range(0))
    nplc_DCV_100mV = list(range(0))
    nplc_Rogowski = list(range(0))
    PT_1000_mode = PT1000mode
    ch_list = ch
    alias_list = alias
    sensor_list = s
    type_list = t
    daq_sensor_types = types
    daq_nplc_list = nplc
    if lsync:
        daq_lsync = 'ON, '
    else:
        daq_lsync = 'OFF, '
    if ocom:
        daq_ocom = 'ON, '
    else:
        daq_ocom = 'OFF, '
    if azer:
        daq_azer = 'ON, '
    else:
        daq_azer = 'OFF, '
    if adel:
        daq_adel = 'ON, '
    else:
        daq_adel = 'OFF, '
        

    #this will be the channel string for the measurements
    reading_str = '(@'
    for i in range(len(ch)):
        reading_str = reading_str + ch[i] + ','
    reading_str = reading_str[:-1] + ')'
    print ('reading string : ', reading_str)
    nb_reading_values = len(ch)
    print ('number of DAQ readings = ', nb_reading_values)
    
    ch_list_temp = '(@'
    ch_list_TC_K = '(@'
    ch_list_TC_J = '(@'
    ch_list_ohm = '(@'
    ch_list_PT_100 = '(@'
    ch_list_PT_1000 = '(@'
    ch_list_DCV_100mV = '(@'
    ch_list_DCV_Volt = '(@'
    ch_list_ACV = '(@'
    ch_list_Rogowski = '(@'
    range_list_DCV = list(range(0))
    range_list_Rogowski = list(range(0))
    range_list_ACV = list(range(0))
    nb_K = 0
    nb_J = 0
    nb_PT100 = 0
    nb_PT1000 = 0
    nb_DCV_100mV = 0
    nb_DCV_Volt =  0
    nb_ACV = 0
    nb_Rogowski = 0

    # generate the Keithley channels and range lists
    for i in range(len(ch)):
        if s[i] == 'TE':
            ch_list_temp = ch_list_temp + ch[i] + ','
            ch_nb_TC.append(ch[i])
            nplc_TE.append(daq_nplc_list[i])
            if t[i] == 'K':
                nb_K += 1
                ch_list_TC_K = ch_list_TC_K + ch[i] + ','
            if t[i] == 'J':
                nb_J += 1
                ch_list_TC_J = ch_list_TC_J + ch[i] + ','            
        if s[i] == 'PT':
            ch_list_ohm = ch_list_ohm + ch[i] + ','
            if t[i] == '100':
                nb_PT100 += 1
                ch_list_PT_100 = ch_list_PT_100 + ch[i] + ','
                ch_nb_PT_100.append(ch[i])
                nplc_PT_100.append(daq_nplc_list[i])
            if t[i] == '1000':
                nb_PT1000 += 1
                ch_list_PT_1000 = ch_list_PT_1000 + ch[i] + ','   
                ch_nb_PT_1000.append(ch[i])
                nplc_PT_1000.append(daq_nplc_list[i])
        if s[i] == 'DCV-100mV':
            ch_list_DCV_100mV = ch_list_DCV_100mV + ch[i] + ','
            ch_nb_DCV_100mV.append(ch[i])
            nplc_DCV_100mV.append(daq_nplc_list[i])
            nb_DCV_100mV += 1
        if s[i] == 'DCV':
            ch_list_DCV_Volt = ch_list_DCV_Volt + ch[i] + ','
            ch_nb_DCV_Volt.append(ch[i])
            nplc_DCV_Volt.append(daq_nplc_list[i])
            range_list_DCV.append(t[i])
            nb_DCV_Volt += 1
        if s[i] == 'ACV':
            ch_list_ACV = ch_list_ACV + ch[i] + ','
            ch_nb_ACV.append(ch[i])
            range_list_ACV.append(t[i])
            nb_ACV += 1   
        if s[i] == 'Rogowski':
            ch_list_Rogowski = ch_list_Rogowski + ch[i] + ','
            ch_nb_Rogowski.append(ch[i])
            nplc_Rogowski.append(daq_nplc_list[i])
            range_list_Rogowski.append(t[i])
            nb_Rogowski += 1            
    
            
    ch_list_temp = ch_list_temp[:-1] + ')'
    ch_list_TC_K = ch_list_TC_K[:-1] + ')'
    ch_list_TC_J = ch_list_TC_J[:-1] + ')'
    ch_list_ohm = ch_list_ohm[:-1] + ')'
    ch_list_PT_100 = ch_list_PT_100[:-1] + ')'
    ch_list_PT_1000 = ch_list_PT_1000[:-1] + ')'
    ch_list_DCV_100mV = ch_list_DCV_100mV[:-1] + ')'
    ch_list_DCV_Volt = ch_list_DCV_Volt[:-1] + ')'
    ch_list_ACV = ch_list_ACV[:-1] + ')'
    ch_list_Rogowski = ch_list_Rogowski[:-1] + ')'
    print ('Keithley NPLC(s): ', daq_nplc_list)
    print ('Keithley sensor list: ', sensor_list)
    print ('Keithley range list: ', type_list)
    print ('Keithley TE channel list: ', ch_list_temp)  
    print ('Keithley TE - K channel list: ', ch_list_TC_K)
    print ('Keithley TE - J channel list: ', ch_list_TC_J)
    print ('Keithley PT channel list: ', ch_list_ohm)
    print ('Keithley PT-100 channel list: ', ch_list_PT_100)
    print ('Keithley PT-1000 channel list: ', ch_list_PT_1000)
    print ('Keithley DCV-100mV channel list: ', ch_list_DCV_100mV)
    print ('Keithley DCV-Volt channel list: ', ch_list_DCV_Volt)
    print ('Keithley Rogowski channel list: ', ch_list_Rogowski)
    print ('Keithley ACV channel list: ', ch_list_ACV)
    
    cm_list = list(range(0))
    cm_list.append(':SYSTEM:CLEAR\n')
    cm_list.append('FORM:DATA ASCII\n')
    
    if nb_K !=0 or nb_J != 0:
        cm_list.append('FUNC "TEMP", ' + ch_list_temp + '\n')
        cm_list.append('TEMP:TRAN TC, ' + ch_list_temp + '\n')
        if nb_K != 0:
            cm_list.append('TEMP:TC:TYPE K, ' + ch_list_TC_K + '\n')
        if nb_J != 0:    
            cm_list.append('TEMP:TC:TYPE J, ' + ch_list_TC_J + '\n')
        cm_list.append('TEMP:UNIT CELS, ' + ch_list_temp + '\n')
        # cm_list.append('TEMP:TC:RJUN:RSEL INT, ' + ch_list_temp + '\n')
        cm_list.append('TEMP:TC:RJUN:RSEL SIM, ' + ch_list_temp + '\n')
        cm_list.append('TEMP:TC:RJUN:SIM 0, ' + ch_list_temp + '\n')
        
        cm_list.append('TEMP:AVER OFF, ' + ch_list_temp + '\n')
        cm_list.append('TEMP:LINE:SYNC ' + daq_lsync + ch_list_temp + '\n')
        cm_list.append('TEMP:OCOM ' + daq_ocom + ch_list_temp + '\n')
        cm_list.append('TEMP:AZER ' + daq_azer + ch_list_temp + '\n')
        #if not azer:
            #cm_list.append('AZER:ONCE' + '\n')
        cm_list.append('TEMP:DEL:AUTO ' + daq_adel + ch_list_temp + '\n')
        
        for i in range(nb_K+nb_J):
            str_nplc = str(nplc_TE[i])
            c = '(@' + ch_nb_TC[i] + ')\n'
            cm_list.append('TEMP:NPLC ' + str_nplc + ' , ' + c) 
    
    if nb_PT100 != 0:
        ## note: PT-100 can be read out as temperature sensor
        cm_list.append('FUNC "TEMP", ' + ch_list_PT_100 + '\n')
        cm_list.append('TEMP:TRAN FRTD, '+ ch_list_PT_100 + '\n')
        cm_list.append('TEMP:RTD:FOUR PT100, ' + ch_list_PT_100 + '\n')
        cm_list.append('TEMP:LINE:SYNC ' + daq_lsync + ch_list_PT_100 + '\n')
        cm_list.append('TEMP:OCOM ' + daq_ocom + ch_list_PT_100 + '\n')
        cm_list.append('TEMP:AZER ' + daq_azer + ch_list_PT_100 + '\n')
        #if not azer:
            #cm_list.append('AZER:ONCE' + '\n')
        cm_list.append('TEMP:DEL:AUTO ' + daq_adel + ch_list_PT_100 + '\n')
        for i in range(nb_PT100):
            str_nplc = str(nplc_PT_100[i])
            c = '(@' + ch_nb_PT_100[i] + ')\n'
            cm_list.append('TEMP:NPLC ' + str_nplc + ' , ' + c)         
        
    if nb_PT1000 != 0:
        # PT-1000 as 4 wire resistance
        if PT_1000_mode == 'R' or PT_1000_mode == 'R+T':
            cm_list.append('FUNC "FRES", ' + ch_list_PT_1000 + '\n')
            cm_list.append('FRES:RANG 10e3, ' + ch_list_PT_1000 + '\n')
            cm_list.append('FRES:LINE:SYNC ' + daq_lsync + ch_list_PT_1000 + '\n')
            cm_list.append('FRES:OCOM ' + daq_ocom + ch_list_PT_1000 + '\n')
            cm_list.append('FRES:AZER ' + daq_azer + ch_list_PT_1000 + '\n')
            #if not azer:
                #cm_list.append('AZER:ONCE' + '\n')
            cm_list.append('FRES:DEL:AUTO ' + daq_adel + ch_list_PT_1000 + '\n')
            cm_list.append('FRES:AVER OFF, ' + ch_list_PT_1000 + '\n')
            for i in range(nb_PT1000):
                str_nplc = str(nplc_PT_1000[i])
                c = '(@' + ch_nb_PT_1000[i] + ')\n'
                cm_list.append('FRES:NPLC ' + str_nplc + ' , ' + c)    
        #PT1000 calculated inside DAQ
        if PT_1000_mode == 'T':
            cm_list.append('FUNC "TEMP", ' + ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:TRAN FRTD, '+ ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:RTD:FOUR USER, ' + ch_list_PT_1000 + '\n')

            cm_list.append('TEMP:RTD:ALPH 0.00385055, ' + ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:RTD:BETA 0.10863, ' + ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:RTD:DELT 1.4999, ' + ch_list_PT_1000 + '\n')

            # neu ??
            #cm_list.append('TEMP:RTD:ALPH 0.0039022, ' + ch_list_PT_1000 + '\n')
            #cm_list.append('TEMP:RTD:BETA 0.0, ' + ch_list_PT_1000 + '\n')
            #cm_list.append('TEMP:RTD:DELT 0.148659, ' + ch_list_PT_1000 + '\n')
            
            cm_list.append('TEMP:RTD:ZERO 1000, ' + ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:LINE:SYNC ' + daq_lsync + ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:OCOM ' + daq_ocom + ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:AZER ' + daq_azer + ch_list_PT_1000 + '\n')
            #if not azer:
                #cm_list.append('AZER:ONCE' + '\n')
            cm_list.append('TEMP:DEL:AUTO ' + daq_adel + ch_list_PT_1000 + '\n')
            cm_list.append('TEMP:AVER OFF, ' + ch_list_PT_1000 + '\n')
            for i in range(nb_PT1000):
                str_nplc = str(nplc_PT_1000[i])
                c = '(@' + ch_nb_PT_1000[i] + ')\n'
                cm_list.append('TEMP:NPLC ' + str_nplc + ' , ' + c)        
        
    
    if nb_DCV_100mV != 0:
        cm_list.append('FUNC "VOLT:DC", ' + ch_list_DCV_100mV + '\n')
        cm_list.append('VOLT:RANG 100e-3, ' + ch_list_DCV_100mV + '\n')
        cm_list.append('VOLT:LINE:SYNC ' + daq_lsync + ch_list_DCV_100mV + '\n')
        cm_list.append('VOLT:AZER ' + daq_azer + ch_list_DCV_100mV + '\n')
        #if not azer:
            #cm_list.append('AZER:ONCE' + '\n')
        cm_list.append('VOLT:AVER OFF, ' + ch_list_DCV_100mV + '\n')
        cm_list.append('VOLT:DEL:AUTO ' + daq_adel + ch_list_DCV_100mV + '\n')
        for i in range(nb_DCV_100mV):
            str_nplc = str(nplc_DCV_100mV[i])
            c = '(@' + ch_nb_DCV_100mV[i] + ')\n'
            cm_list.append('VOLT:NPLC ' + str_nplc + ', ' + c)         
        
        
    if nb_DCV_Volt != 0:
        cm_list.append('FUNC "VOLT:DC", ' + ch_list_DCV_Volt + '\n')
        cm_list.append('VOLT:LINE:SYNC ' + daq_lsync + ch_list_DCV_Volt + '\n')
        cm_list.append('VOLT:AZER ' + daq_azer + ch_list_DCV_Volt + '\n')
        #if not azer:
            #cm_list.append('AZER:ONCE' + '\n')
        cm_list.append('VOLT:AVER OFF, ' + ch_list_DCV_Volt + '\n')
        cm_list.append('VOLT:DEL:AUTO ' + daq_adel + ch_list_DCV_Volt + '\n')
        for i in range(nb_DCV_Volt):
            str_nplc = str(nplc_DCV_Volt[i])
            c = '(@' + ch_nb_DCV_Volt[i] + ')\n'
            cm_list.append('VOLT:NPLC ' + str_nplc + ', ' + c)                
            l = len(range_list_DCV[i])
            if range_list_DCV[i][l-1:] == 'V':
                r = range_list_DCV[i][:-1]
                cm_list.append('VOLT:RANG ' + r + ', ' + c)
            else:
                #Auto
                cm_list.append('VOLT:RANG:AUTO ON, ' + c)
    
    if nb_ACV != 0:
        cm_list.append('FUNC "VOLT:AC", ' + ch_list_ACV + '\n')
        cm_list.append('VOLT:AC:AVER OFF, ' + ch_list_ACV + '\n')
        cm_list.append('VOLT:AC:DEL:AUTO ' + daq_adel + ch_list_ACV + '\n')
        
        for i in range(nb_ACV):
            c = '(@' + ch_nb_ACV[i] + ')\n'
            l = len(range_list_ACV[i])
            if range_list_ACV[i][l-1:] == 'V':
                r = range_list_ACV[i][:-1]
                cm_list.append('VOLT:AC:RANG ' + r + ', ' + c)
            else:
                #Auto
                cm_list.append('VOLT:AC:RANG:AUTO ON, ' + c)        
        #cm_list.append('VOLT:AC:RANG:AUTO ON, ' + ch_list_ACV + '\n')
        #cm_list.append('VOLT:AC:RANG 10, ' + ch_list_ACV + '\n')
        # only signals with frequency greater than the detector bandwidth are measured
        # detectors bandwith: 3, 30 or 300 Hz, default = 3
        cm_list.append('VOLT:AC:DET:BAND 300, ' + ch_list_ACV + '\n')

    if nb_Rogowski != 0:
        cm_list.append('FUNC "VOLT:DC", ' + ch_list_Rogowski + '\n')
        cm_list.append('VOLT:LINE:SYNC ' + daq_lsync + ch_list_Rogowski + '\n')
        cm_list.append('VOLT:AZER ' + daq_azer + ch_list_Rogowski + '\n')
        #if not azer:
            #cm_list.append('AZER:ONCE' + '\n')
        cm_list.append('VOLT:DEL:AUTO ' + daq_adel + ch_list_Rogowski + '\n')
        cm_list.append('VOLT:AVER OFF, ' + ch_list_Rogowski + '\n')
        for i in range(nb_Rogowski):
            str_nplc = str(nplc_Rogowski[i])
            c = '(@' + ch_nb_Rogowski[i] + ')\n'
            cm_list.append('VOLT:NPLC ' + str_nplc + ', ' + c)                
            l = len(range_list_Rogowski[i])
            if range_list_Rogowski[i][l-1:] == 'V':
                r = range_list_Rogowski[i][:-1]
                cm_list.append('VOLT:RANG ' + r + ', ' + c)
            else:
                #Auto
                r = range_list_Rogowski[i]
                cm_list.append('VOLT:RANG:AUTO ON, ' + ch_list_Rogowski + '\n')
            
    cm_list.append('DISP:CLE\n')
    cm_list.append('DISP:LIGH:STAT ON50\n')
    #cm_list.append('DISP:SCR HOME_LARG\n')
    #cm_list.append('DISP:SCR PROC\n')
    cm_list.append('DISP:USER1:TEXT "ready to start ..."\n')
    #cm_list.append('DISP:BUFF:ACT "defbuffer1"\n')
    #cm_list.append('ROUTE:CHAN:CLOSE (@101)\n')
    #cm_list.append('DISP:WATC:CHAN (@101)\n')
    
    if not test_daq:
        for i in range(len(cm_list)):
            if debug_daq:
                print ('writing to COM port: ', cm_list[i])
            if interface == 'LAN':
                ser_daq.write(cm_list[i])
            else:
                ser_daq.write(cm_list[i].encode())
    
 
###########################################################################
def Write_LSYNC(u, state):
###########################################################################
    if state == True: 
        onoff = 'ON, '
    else:
        onoff = 'OFF, '
    if daq_sensor_types[u] == 'TE':
        cmd = 'TEMP:LINE:SYNC '+ onoff + ch_list_temp + '\n'
    if daq_sensor_types[u] == 'PT-100':
        cmd = 'TEMP:LINE:SYNC ' + onoff + ch_list_PT_100 + '\n' 
    if daq_sensor_types[u] == 'PT-1000':
        if PT_1000_mode == 'R' or PT_1000_mode == 'R+T':
            cmd = 'FRES:LINE:SYNC ' + onoff + ch_list_PT_1000 + '\n'     
        if PT_1000_mode == 'T':
            cmd = 'TEMP:LINE:SYNC ' + onoff + ch_list_PT_1000 + '\n'     
    if daq_sensor_types[u] == 'DCV-100mV':
        cmd = 'VOLT:LINE:SYNC ' + onoff + ch_list_DCV_100mV + '\n' 
    if daq_sensor_types[u] == 'DCV':
        cmd = 'VOLT:LINE:SYNC ' + onoff + ch_list_DCV_Volt + '\n'  
    if daq_sensor_types[u] == 'Rogowski':
        cmd = 'VOLT:LINE:SYNC ' + onoff + ch_list_Rogowski + '\n'  
    if not test_daq:
        if debug_daq:
            print ('Sending to COM: ' + cmd)
        if interface == 'LAN':
            ser_daq.write(cmd)
        else:
            ser_daq.write(cmd.encode())
    print ('LSYNC ' + daq_sensor_types[u] + ' : ', state)   
            
###########################################################################
def Write_OCOM(u, state):
###########################################################################
    if state == True: 
        onoff = 'ON, '
    else:
        onoff = 'OFF, '
    if daq_sensor_types[u] == 'TE':
        cmd = 'TEMP:OCOM '+ onoff + ch_list_temp + '\n'
    if daq_sensor_types[u] == 'PT-100':
        cmd = 'TEMP:OCOM ' + onoff + ch_list_PT_100 + '\n' 
    if daq_sensor_types[u] == 'PT-1000':
        if PT_1000_mode == 'R' or PT_1000_mode == 'R+T':
            cmd = 'FRES:OCOM ' + onoff + ch_list_PT_1000 + '\n'     
        if PT_1000_mode == 'T':
            cmd = 'TEMP:OCOM ' + onoff + ch_list_PT_1000 + '\n'     
    if not test_daq:
        if debug_daq:
            print ('Sending to COM: ' + cmd)
        if interface == 'LAN':
            ser_daq.write(cmd)
        else:
            ser_daq.write(cmd.encode())
    print ('OCOM ' + daq_sensor_types[u] + ' : ', state)  
 
 
###########################################################################
def Write_NPLC(u, val):
########################################################################### 
    cm_list = list(range(0))
    val_str = str(val)
    if sensor_list[u] == 'TE':
        cm_list.append('TEMP:NPLC ' + val_str + ', (@' + ch_list[u] + ')\n')
    if sensor_list[u] == 'PT' and type_list[u] == '100':
        cm_list.append('TEMP:NPLC ' + val_str + ', (@' + ch_list[u] + ')\n')
    if sensor_list[u] == 'PT' and type_list[u] == '1000':
        if PT_1000_mode == 'R' or PT_1000_mode == 'R+T':
            cm_list.append('FRES:NPLC ' + val_str + ', (@' + ch_list[u] + ')\n')        
        if PT_1000_mode == 'T':
            cm_list.append('TEMP:NPLC ' + val_str + ', (@' + ch_list[u] + ')\n')
    if sensor_list[u] == 'DCV-100mV':
        cm_list.append('VOLT:NPLC ' + val_str + ', (@' + ch_list[u] + ')\n')
    if sensor_list[u] == 'DCV':
        cm_list.append('VOLT:NPLC ' + val_str + ', (@' + ch_list[u] + ')\n')
    if sensor_list[u] == 'Rogowski':
        cm_list.append('VOLT:NPLC ' + val_str + ', (@' + ch_list[u] + ')\n')               
    if not test_daq:
        for i in range(len(cm_list)):
            if debug_daq:
                print ('Sending to COM: ' + cm_list[i])
            if interface == 'LAN':
                ser_daq.write(cm_list[i])
            else:
                ser_daq.write(cm_list[i].encode())
    print ('NPLC ' + ch_list[u] + ' (' + alias_list[u] + ') : ' + val_str)    
        
   
###########################################################################
def Write_Filter_Count(u, val):
###########################################################################
    cm_list = list(range(0))
    val_str = str(val)
    if daq_sensor_types[u] == 'TE':
        cm_list.append('TEMP:AVER:COUNT ' + val_str + ', ' + ch_list_temp + '\n')
    if daq_sensor_types[u] == 'PT-100':
        cm_list.append('TEMP:AVER:COUNT ' + val_str + ch_list_PT_100 + '\n')
    if daq_sensor_types[u] == 'PT-1000':
        if PT_1000_mode == 'R' or PT_1000_mode == 'R+T':
            cm_list.append('FRES:AVER:COUNT ' + val_str + ch_list_PT_1000 + '\n')
        if PT_1000_mode == 'T':
            cm_list.append('TEMP:AVER:COUNT ' + val_str + ch_list_PT_1000 + '\n')
    if daq_sensor_types[u] == 'DCV-100mV':
        cm_list.append('VOLT:AVER:COUNT ' + val_str + ch_list_DCV_100mV + '\n')
    if daq_sensor_types[u] == 'DCV':
        cm_list.append('VOLT:AVER:COUNT ' + val_str + ch_list_DCV_Volt + '\n')
    if daq_sensor_types[u] == 'Rogowski':
        cm_list.append('VOLT:AVER:COUNT ' + val_str + ch_list_Rogowski + '\n')         
    if not test_daq:
        for j in range(len(cm_list)):
            if debug_daq:
                print ('Sending to COM: ' + cm_list[j])    
            if interface == 'LAN':
                ser_daq.write(cm_list[j])
            else:
                ser_daq.write(cm_list[j].encode())
    print ('Filter count(s) ' + daq_sensor_types[u] + ' : ' + val_str) 
            
###########################################################################
def Write_Filter_State(u, state):
###########################################################################
    cm_list = list(range(0))
    if daq_sensor_types[u] == 'TE':
        if state == 'OFF':
            cm_list.append('TEMP:AVER OFF, ' + ch_list_temp + '\n')
        elif state == 'repeat':
            cm_list.append('TEMP:AVER ON, ' + ch_list_temp + '\n')
            cm_list.append('TEMP:AVER:TCON REP, ' + ch_list_temp + '\n')
        elif state == 'moving':
            cm_list.append('TEMP:AVER ON, ' + ch_list_temp + '\n')
            cm_list.append('TEMP:AVER:TCON MOV, ' + ch_list_temp + '\n')
    if daq_sensor_types[u] == 'PT-100':
        if state == 'OFF':
            cm_list.append('TEMP:AVER OFF, ' + ch_list_PT_100 + '\n')
        elif state == 'repeat':
            cm_list.append('TEMP:AVER ON, ' + ch_list_PT_100 + '\n')
            cm_list.append('TEMP:AVER:TCON REP, ' + ch_list_PT_100 + '\n')
        elif state == 'moving':
            cm_list.append('TEMP:AVER ON, ' + ch_list_PT_100 + '\n')
            cm_list.append('TEMP:AVER:TCON MOV, ' + ch_list_PT_100 + '\n')
    if daq_sensor_types[u] == 'PT-1000':
        if PT_1000_mode == 'R' or PT_1000_mode == 'R+T':
            if state == 'OFF':
                cm_list.append('FRES:AVER OFF, ' + ch_list_PT_1000 + '\n')
            elif state == 'repeat':
                cm_list.append('FRES:AVER ON, ' + ch_list_PT_1000 + '\n')
                cm_list.append('FRES:AVER:TCON REP, ' + ch_list_PT_1000 + '\n')
            elif state == 'moving':
                cm_list.append('FRES:AVER ON, ' + ch_list_PT_1000 + '\n')
                cm_list.append('FRES:AVER:TCON MOV, ' + ch_list_PT_1000 + '\n')    
        if PT_1000_mode == 'T':
            if state == 'OFF':
                cm_list.append('TEMP:AVER OFF, ' + ch_list_PT_1000 + '\n')
            elif state == 'repeat':
                cm_list.append('TEMP:AVER ON, ' + ch_list_PT_1000 + '\n')
                cm_list.append('TEMP:AVER:TCON REP, ' + ch_list_PT_1000 + '\n')
            elif state == 'moving':
                cm_list.append('TEMP:AVER ON, ' + ch_list_PT_1000 + '\n')
                cm_list.append('TEMP:AVER:TCON MOV, ' + ch_list_PT_1000 + '\n')    
    if daq_sensor_types[u] == 'DCV-100mV':
        if state == 'OFF':
            cm_list.append('VOLT:AVER OFF, ' + ch_list_DCV_100mV + '\n')
        elif state == 'repeat':
            cm_list.append('VOLT:AVER ON, ' + ch_list_DCV_100mV + '\n')
            cm_list.append('VOLT:AVER:TCON REP, ' + ch_list_DCV_100mV + '\n')
        elif state == 'moving':
            cm_list.append('VOLT:AVER ON, ' + ch_list_DCV_100mV + '\n')
            cm_list.append('VOLT:AVER:TCON MOV, ' + ch_list_DCV_100mV + '\n')                
    if daq_sensor_types[u] == 'DCV-Volt':
        if state == 'OFF':
            cm_list.append('VOLT:AVER OFF, ' + ch_list_DCV_Volt + '\n')
        elif state == 'repeat':
            cm_list.append('VOLT:AVER ON, ' + ch_list_DCV_Volt + '\n')
            cm_list.append('VOLT:AVER:TCON REP, ' + ch_list_DCV_Volt + '\n')
        elif state == 'moving':
            cm_list.append('VOLT:AVER ON, ' + ch_list_DCV_Volt + '\n')
            cm_list.append('VOLT:AVER:TCON MOV, ' + ch_list_DCV_Volt + '\n') 
    if daq_sensor_types[u] == 'Rogowski':
        if state == 'OFF':
            cm_list.append('VOLT:AVER OFF, ' + ch_list_Rogowski + '\n')
        elif state == 'repeat':
            cm_list.append('VOLT:AVER ON, ' + ch_list_Rogowski + '\n')
            cm_list.append('VOLT:AVER:TCON REP, ' + ch_list_Rogowski + '\n')
        elif state == 'moving':
            cm_list.append('VOLT:AVER ON, ' + ch_list_Rogowski + '\n')
            cm_list.append('VOLT:AVER:TCON MOV, ' + ch_list_Rogowski + '\n')         
        
    if not test_daq:
        for j in range(len(cm_list)):
            if debug_daq:
                print ('Sending to COM: ' + cm_list[j])  
            if interface == 'LAN':
                ser_daq.write(cm_list[j])
            else:
                ser_daq.write(cm_list[j].encode())
    print ('Filter state ' + daq_sensor_types[u] + ' : ' + state) 
        
###########################################################################
def Write_AZER(u, state):
###########################################################################
    if state == True: 
        onoff = 'ON, '
    else:
        onoff = 'OFF, '
    if daq_sensor_types[u] == 'TE':
        cmd = 'TEMP:AZER '+ onoff + ch_list_temp + '\n'
    if daq_sensor_types[u] == 'PT-100':
        cmd = 'TEMP:AZER ' + onoff + ch_list_PT_100 + '\n' 
    if daq_sensor_types[u] == 'PT-1000':
        if PT_1000_mode == 'R' or PT_1000_mode == 'R+T':
            cmd = 'FRES:AZER ' + onoff + ch_list_PT_1000 + '\n'     
        if PT_1000_mode == 'T':
            cmd = 'TEMP:AZER ' + onoff + ch_list_PT_1000 + '\n'     
    if daq_sensor_types[u] == 'DCV-100mV':
        cmd = 'VOLT:AZER ' + onoff + ch_list_DCV_100mV + '\n' 
    if daq_sensor_types[u] == 'DCV':
        cmd = 'VOLT:AZER ' + onoff + ch_list_DCV_Volt+ '\n'         
    if daq_sensor_types[u] == 'Rogowski':
        cmd = 'VOLT:AZER ' + onoff + ch_list_Rogowski+ '\n'              
    if not test_daq:
        if debug_daq:
            print ('Sending to COM: ' + cmd)
        if interface == 'LAN':
            ser_daq.write(cmd)
        else:
            ser_daq.write(cmd.encode())
    print ('AZER ' + daq_sensor_types[u] + ' : ', state)  
        
    
    
def reset_daq():
    print ('Reset DAQ 6510')
    cm_list = list(range(0))
    cm_list.append('*RST\n')
    cm_list.append('DISP:USER1:TEXT "ready  to start ..."\n')
    if not test_daq:
        for i in range(len(cm_list)):
            if debug_daq:
                print ('writing to COM : ' + cm_list[i])
            if interface == 'LAN':
                ser_daq.write(cm_list[i])
            else:
                ser_daq.write(cm_list[i].encode())

def message_daq_display():
    cm_list = list(range(0))
    cm_list.append('DISP:USER1:TEXT "sampling ..."\n')
    if not test_daq:
        for i in range(len(cm_list)):
            if debug_daq:
                print ('writing to COM : ' + cm_list[i])
            if interface == 'LAN':
                ser_daq.write(cm_list[i])
            else:
                ser_daq.write(cm_list[i].encode())
    
def idn_daq():
    cmd = '*IDN?\n'
    if not test_daq:
        if debug_daq:
            print ('writing to COM : ' + cmd)
        if interface == 'LAN':
            ser_daq.write(cmd)
            instrument = ser_daq.read()
        else:
            ser_daq.write(cmd.encode())
            instrument = ser_daq.readline().decode()
        if debug_daq:
            print ('reading from COM : ' , instrument)
        print ('IDN: ', instrument)
    
def idn_card_1():
    cmd = 'SYST:CARD1:IDN?\n'
    if not test_daq:
        if debug_daq:
            print ('writing to COM : ' + cmd)    
        if interface == 'LAN':
            ser_daq.write(cmd)
            instrument = ser_daq.read()
        else:
            ser_daq.write(cmd.encode())
            instrument = ser_daq.readline().decode()
        if debug_daq:
            print ('reading from COM : ', instrument)
        print ('Card-01: ', instrument)

def idn_card_2():
    cmd = 'SYST:CARD2:IDN?\n'
    if not test_daq:
        if debug_daq:
            print ('writing to COM : ' + cmd)   
        if interface == 'LAN':
            ser_daq.write(cmd)
            instrument = ser_daq.read()
        else:
            ser_daq.write(cmd.encode())
            instrument = ser_daq.readline().decode()
        if debug_daq:
            print ('reading from COM : ', instrument)
        print ('Card-02: ', instrument)
    
    
