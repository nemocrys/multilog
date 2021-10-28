import serial
import random
import re

global ser_py, debug_arduino, test_arduino


def my_split(s):
    return filter(None, re.split(r'(\d+)', s))


###########################################################################
def Init_Arduino(i, com, rate, bits, stop, parity, dbg, test):
###########################################################################
    
    global ser_py, debug_arduino, test_arduino
        
    debug_arduino = dbg
    test_arduino = test
    if i == 0:
        ser_py = list(range(0))
    portName = 'COM'+str(com)
    try:
        serial.Serial(port=portName)
    except serial.SerialException:
        print ('Port ' + portName + ' not present')
        if not test_arduino:
            quit()
    
    if not test_arduino:
        ser_py_ = serial.Serial(
            port = portName,
            baudrate = int(rate),
            parity = parity,
            stopbits = int(stop),
            bytesize = int(bits),
            timeout = 2.0)
            
        ser_py.append(ser_py_)



###########################################################################    
def my_Read_Arduino(i, end_id):
###########################################################################    
    
    end_of_read = False
    st = ''
    while not end_of_read:
        char = ser_py[i].read(1).decode()
        st = st + char
        st = st.replace('\r', '\\r')
        st = st.replace('\n', '\\n')
        if end_id in st :
            end_of_read = True
    return (st)
    
###########################################################################
def Read_Arduino(i, cmd_list, read_id_list, end_id_list, position_list, separator_list):
###########################################################################
    
    result = list(range(0))
    for j in range(len(cmd_list)):
        if not test_arduino:
            if debug_arduino:
                print ('Sending to ' + ser_py[i].port + ': ' + cmd_list[j])
            ser_py[i].write((cmd_list[j]+'\r').encode())
            #_temp = ser_py[i].readline().decode()
            #_temp = _temp.rstrip()
            _temp = my_Read_Arduino(i, end_id_list[j])
        else:
            if cmd_list[j] == 'g':
                _temp = 'g=41.19\\r\\n'
            elif cmd_list[j] =='c':
                _temp = 'c=24.50' 
            elif cmd_list[j] == 'h':
                _temp = 'h=1'
            elif cmd_list[j] =='IN_PV_1':
                _temp = '0.0 1' 
            elif cmd_list[j] =='GN_PV_2':
                _temp = '25.0 2'
            elif cmd_list[j] =='HN_X':
                _temp = '14.5XSTART=23.4;99.99;15;XEND77.7;'                        
            else:
                _temp = ''
            
        if debug_arduino:
            print ('reading from COM port: ', _temp)
         
        #_temp = _temp.replace('\r', '\\r')
        #_temp = _temp.replace('\n', '\\n')            
            
        if read_id_list[j] in _temp:
            pos = _temp.find(read_id_list[j])
            pos2 = pos + len(read_id_list[j])
            temp = _temp[pos2:]
        if end_id_list[j] in temp:
            pos = temp.find(end_id_list[j])
            temp = temp[:pos]
        if position_list[j] != '':
            temp = temp.split(separator_list[j])[int(position_list[j])-1]
        else:
            z = 0
            nb_found = False
            temp_ = temp
            while not nb_found:
                try:
                    temp_ = temp[:len(temp)-z]
                    nb = float(temp_)
                    nb_found = True
                    temp = temp_
                except ValueError:
                    z += 1
                    continue
                
        if debug_arduino:
            print ('filtered from COM port: ', temp)
            
        result.append(float(temp))
    return (result) 
