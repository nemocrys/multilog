from copy import deepcopy
import datetime
import logging
import numpy as np
import minimalmodbus
from serial import Serial, SerialException
import serial
import yaml

logger = logging.getLogger(__name__)


class SerialMock:
    """This class is used to mock a serial interface for debugging purposes."""

    def write(self, _):
        pass

    def readline(self):
        return "".encode()
    

class PyrometerDias:
    """Dias pyrometer"""

    def __init__(self, config, name="PyrometerDias"):
        """Setup serial interface, configure device.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
        """
        logger.info(f"Initializing PyrometerDias device '{name}'")
        self.config = config
        self.name = name
        self.emissivity = self.config['emissivity']
        self.transmissivity = self.config['transmissivity']
        self.latestSample = np.nan

        if self.config.get("serial-interface") != None: # serial conection
            self.meas_data = []
            
            try:
                self.instrument = minimalmodbus.Instrument(self.config['serial-interface']['port'], 1)
                parity = {'E': serial.PARITY_EVEN, 'N': serial.PARITY_NONE}
                self.instrument.serial.parity   = parity[self.config['serial-interface']['parity']]
                self.instrument.serial.baudrate = self.config['serial-interface']['baudrate']
                self.instrument.serial.bytesize = self.config['serial-interface']['bytesize']
                self.instrument.serial.stopbits = self.config['serial-interface']['stopbits']
                self.instrument.serial.timeout  = self.config['serial-interface']['timeout']

                self.write_e(self.emissivity)
                self.write_t(self.transmissivity)

            except SerialException as e:
                logger.exception(f"Connection to {self.name} not possible.")
                self.serial = SerialMock()
                


    def write_e(self, e):
        #print('Sende den Emissionsgrad an das Pyrometer')
        try:
            if e*100 > 100 or e*100 < 1:
                logger.error(f"{self.name}: new emiemission value out of bound.")
            self.instrument.write_register(258, e*100, 1)
        except SerialException as e:
            logger.exception(f"{self.name}: changing of emission not possible.")

    def write_t(self, t):
        #print('Sende den Transmissionsgrad an das Pyrometer')
        try:
            if t*100 > 100 or t*100 < 50:
                logger.error(f"{self.name}: new transmisson value out of bound.")
            self.instrument.write_register(261, t*100, 1)
        except SerialException as e:
            logger.exception(f"{self.name}: changing of transmission not possible.")
            

    def read_e(self):
        #print('Hole den Emissionsgrad vom Pyrometer')
        e = self.instrument.read_register(258, 3)
        return e

    def read_t(self):
        #print('Hole den Transmissionsgrad vom Pyrometer')
        t = self.instrument.read_register(261, 1)
        return t

    def read_T(self):
        #print('Hole die Temperatur vom Pyrometer')
        MessT = self.instrument.read_register(257, 0)
        T = (MessT - 4370)/16
        return T
    
    def closeEvent(self, event):                                                                
        self.instrument.serial.close()

        
    def sample(self):
        """Read temperature form device.

        Returns:
            float: temperature reading.
        """
        
        try:
            val = self.read_T()
        except Exception as e:
            logger.exception(f"Could not sample PyrometerDias.")
            val = np.nan

        self.setLatestSample(val)
        return val

    def setLatestSample(self, sampling):
        self.latestSample = sampling
        
    def getLatestSample(self):
        return self.latestSample

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        units = "# datetime,s,DEG C,\n"
        header = "time_abs,time_rel,Temperature,\n"
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(units)
            f.write(header)
        #self.write_nomad_file(directory)

    def save_measurement(self, time_abs, time_rel, sampling):
        """Write measurement data to file.

        Args:
            time_abs (datetime): measurement timestamp.
            time_rel (float): relative time of measurement.
            sampling (float): temperature, as returned from sample()
        """
        timediff = (
            datetime.datetime.now(datetime.timezone.utc).astimezone() - time_abs
        ).total_seconds()
        if timediff > 1:
            logger.warning(
                f"{self.name} save_measurement: time difference between event and saving of {timediff} seconds for samplint timestep {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')} - {time_rel}"
            )
        self.meas_data.append(sampling)
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{sampling},\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)
