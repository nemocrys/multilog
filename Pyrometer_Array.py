import serial
import random
import numpy

global ser_py_array, debug_pyro, test_pyro



###########################################################################
def Init_Pyro_Array(com, rate, bits, stop, parity, dbg, test):
###########################################################################
    
    global ser_py_array, debug_pyro, test_pyro
    
    debug_pyro = dbg
    test_pyro = test
    portName = 'COM'+str(com)
    try:
        serial.Serial(port=portName)
    except serial.SerialException:
        print ('Port ' + portName + ' not present')
        if not test_pyro:
            quit()
    
    if not test_pyro:
        ser_py_array = serial.Serial(
            port = portName,
            baudrate = int(rate),
            parity = parity,
            stopbits = int(stop),
            bytesize = int(bits),            
            timeout = 0.1)
            
    

###########################################################################
def Config_Pyro_Array(i, em):
###########################################################################
# i is the head number, starts with 0
    
    if not test_pyro:
        print ('Pyrometer array head', i+1, ' : ', Get_head_ID(i))
        Write_Pyro_Array_Para(i, 'e', str(em))
    
###########################################################################
def Get_nb_of_head():
###########################################################################
    
    p = '00oc\r'

###########################################################################
def Get_head_ID(i):
###########################################################################
# i is the head number, starts with 0
    
    p = '00A' + str(i+1) + 'sn\r'
    ser_py_array.write(p.encode())
    pyro_head_id = ser_py_array.readline().decode()
    return (pyro_head_id)

###########################################################################
def Get_OK(i):
###########################################################################
    
    answer = ser_py_array.readline().decode()
    print ('Pyrometer array head', str(i+1), ' = ', answer)
    
    
###########################################################################
def Write_Pyro_Array_Para(i, para, str_val):
###########################################################################
### e = emission
### i is the head number, starts with 0    
    
    if para == 'e':
        val = '%05.1f' % float(str_val)
        str_val = str(val).replace('.', '')    
        p = '00A' + str(i+1) + 'em' + str_val + '\r'
    if para == 't90':
        p = '00A' + str(i+1) + 'ez' + str_val + '\r'
    if not test_pyro:
        if debug_pyro:
            print ('Sending to head ' + str(i+1) +': ', p.encode())
        ser_py_array.write(p.encode())
        Get_OK(i)
        answer = Get_Pyro_Array_Para(i, para)
        if para == 'e':
            print ('Pyrometer array head ', str(i+1), ' emission = ', answer)
        if para == 't90':
            print ('Pyrometer array head ', str(i+1), ' t90 = ', answer)     
    else:
        print ('Pyrometer array head ' +str(i+1) + ' parameter: ', p)

        
###########################################################################
def Get_Pyro_Array_Para(i, para):
###########################################################################
### e = emission, t = transmission
    
    if para == 'e':
        p = '00A' + str(i+1) + 'em\r'
    if para == 't90':
        p = '00A' + str(i+1) + 'ez\r'
    if not test_pyro:
        if debug_pyro:
            print ('Sending to pyrometer head ' + str(i+1) + ': ', p.encode())
        ser_py_array.write(p.encode())
        answer = ser_py_array.readline().decode()
        return (answer)
    else:
        print ('Pyrometer array head ' + str(i+1) + ' parameter: ', p)    


###########################################################################
def Read_Pyro_Array(i):
###########################################################################
# i is the head number, starts with 0
    
    p = '00A' + str(i+1) + 'ms\r'
    if not test_pyro:
        if debug_pyro:
            print ('Sending to head ', + str(i+1) + ': ', p.encode())
        ser_py_array.write(p.encode())
        temp = ser_py_array.readline().decode()
        temp = temp[:-1]
        l = len(temp)
        temp = temp[:l-1] + '.' + temp[l-1:]
        if debug_pyro:
            print ('Reading from head ' + str(i+1) + ': ', float(temp))
    else:
        temp = random.uniform(20,22)
    return (float(temp))


