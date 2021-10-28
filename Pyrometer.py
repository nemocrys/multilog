import serial
import random
import numpy

global ser_py, debug_pyro, test_pyro



###########################################################################
def Init_Pyro(i, com, rate, bits, stop, parity, dbg, test):
###########################################################################
    
    global ser_py, debug_pyro, test_pyro
    
    debug_pyro = dbg
    test_pyro = test
    if i == 0:
        ser_py = list(range(0))
    portName = 'COM'+str(com)
    try:
        serial.Serial(port=portName)
    except serial.SerialException:
        print ('Port ' + portName + ' not present')
        if not test_pyro:
            quit()
    
    if not test_pyro:
        ser_py_ = serial.Serial(
            port = portName,
            baudrate = int(rate),
            parity = parity,
            stopbits = int(stop),
            bytesize = int(bits),            
            timeout = 0.1)
            
        ser_py.append(ser_py_)
    
    

###########################################################################
def Config_Pyro(i, em, tr):
###########################################################################

    if not test_pyro:
        print ('Pyrometer ', i+1, ' : ', Get_ID(i))
        Write_Pilot(i, False)
        Write_Pyro_Para(i, 'e', str(em))
        Write_Pyro_Para(i, 't', str(tr))
    
###########################################################################
def Get_Focus(i):
###########################################################################

    p = '00df\r'
    ser_py[i].write(p.encode())
    pyro_focus = ser_py[i].readline().decode()
    return (pyro_focus)

###########################################################################
def Get_ID(i):
###########################################################################
    
    p = '00na\r'
    ser_py[i].write(p.encode())
    pyro_id = ser_py[i].readline().decode()
    return (pyro_id)


###########################################################################
def Get_OK(i):
###########################################################################
    
    answer = ser_py[i].readline().decode()
    print ('Pyrometer ', str(i+1), ' = ', answer)
    
    
###########################################################################
def Write_Pyro_Para(i, para, str_val):
###########################################################################
### e = emission, t = transmission
    
    if para == 'e':
        val = '%05.1f' % float(str_val)
        str_val = str(val).replace('.', '')    
        p = '00em' + str_val + '\r'
    if para == 't':
        val = '%05.1f' % float(str_val)
        str_val = str(val).replace('.', '')    
        p = '00et' + str_val + '\r'
    if para == 't90':
        p = '00ez' + str_val + '\r'
    if not test_pyro:
        if debug_pyro:
            print ('Sending to ' + ser_py[i].port +': ', p.encode())
        ser_py[i].write(p.encode())
        Get_OK(i)
        answer = Get_Pyro_Para(i, para)
        if para == 'e':
            print ('Pyrometer ', str(i+1), ' emission = ', answer)
        if para == 't':
            print ('Pyrometer ', str(i+1), ' transmission = ', answer)     
        if para == 't90':
            print ('Pyrometer ', str(i+1), ' t90 = ', answer)     
    else:
        print ('Pyro ' +str(i+1) + ' parameter: ', p)

        
###########################################################################
def Get_Pyro_Para(i, para):
###########################################################################
### e = emission, t = transmission
    
    if para == 'e':
        p = '00em\r'
    if para == 't':
        p = '00et\r'
    if para == 't90':
        p = '00ez\r'
    if not test_pyro:
        if debug_pyro:
            print ('Sending to ' + ser_py[i].port +': ', p.encode())
        ser_py[i].write(p.encode())
        answer = ser_py[i].readline().decode()
        return (answer)
    else:
        print ('Pyro ' +str(i+1) + ' parameter: ', p)    


###########################################################################
def Read_Pyro(i):
###########################################################################

    p = '00ms\r'
    if not test_pyro:
        if debug_pyro:
            print ('Sending to ' + ser_py[i].port + ': ', p.encode())
        ser_py[i].write(p.encode())
        temp = ser_py[i].readline().decode()
        temp = temp[:-1]
        l = len(temp)
        temp = temp[:l-1] + '.' + temp[l-1:]
        if debug_pyro:
            print ('Reading from ' + ser_py[i].port + ': ', float(temp))
    else:
        temp = random.uniform(20,22)
    return (float(temp))



###########################################################################
def Write_Pilot(i, state):
###########################################################################

    print ('Pilot-'+str(i+1)+' : ' +str(state))
    if not test_pyro:
        if state:
            p = '00la1\r'
        else:
            p = '00la0\r'
        if debug_pyro:
            print ('Sending to ' + ser_py[i].port +': ', p.encode()) 
        ser_py[i].write(p.encode())
        Get_OK(i)