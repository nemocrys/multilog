from copy import deepcopy
import datetime
import logging
import numpy as np
import usbtmc
import yaml

logger = logging.getLogger(__name__)


class SerialMock:
    """This class is used to mock a serial interface for debugging purposes."""

    def write(self, _):
        pass

    def read(self):
        return np.nan

    def ask(self, _):
        return "".encode()


class Keysight:
    """Keysight."""

    def __init__(self, config, name="Keysight"):
        """Setup serial interface, configure device.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
        """
        logger.info(f"Initializing Keysight device '{name}'")
        self.config = config
        self.python_Bib_serial = config["connection"]
        self.device_vid = config["VID"]
        self.device_pid = config["PID"]
        self.device_ad  = config["address"]
        self.device_NAN_Limit   = config['nan-limit_V']
        self.device_NAN_Limit_f = config['nan-limit_f']
        self.name = name
        self.latestSample = np.nan

        self.channel_1_activ = config['channel_active'][1]
        self.channel_2_activ = config['channel_active'][2]
        self.channel_3_activ = config['channel_active'][3]
        self.channel_4_activ = config['channel_active'][4]
        if not type(self.channel_1_activ) == bool and not self.channel_1_activ in [0,1]: self.channel_1_activ = False
        if not type(self.channel_2_activ) == bool and not self.channel_2_activ in [0,1]: self.channel_1_activ = False
        if not type(self.channel_3_activ) == bool and not self.channel_3_activ in [0,1]: self.channel_1_activ = False
        if not type(self.channel_4_activ) == bool and not self.channel_4_activ in [0,1]: self.channel_1_activ = False

        self.meas_data = []

        if self.python_Bib_serial in ['pyvisa', 'usbtmc']:      logger.info(f'The oscilloscope {self.name} uses the Python library {self.python_Bib_serial} for communication!')
        else:                                                   
            logger.warning(f'The selected Python library{self.python_Bib_serial} does not exist for the oscilloscope {self.name}! Set default to pyvisa!')
            self.python_Bib_serial = 'pyvisa'

        try:
            # Aufbau der Schnittstelle durch pyvisa oder usbtmc:
            if self.python_Bib_serial == 'usbtmc':      self.serial =  usbtmc.Instrument(self.device_vid, self.device_pid)
            elif self.python_Bib_serial == 'pyvisa':
                # Import von pyvisa, da die Bibliothek typing_extensions beim Import einen Fehler verursachen kann -> so wird er gelogged!!
                import pyvisa                                 
                resourceManager = pyvisa.ResourceManager()
                self.serial = resourceManager.open_resource(self.device_ad)
        except Exception as e:
            logger.exception(f"Connection to {self.name} not possible.")
            self.serial = SerialMock()
        
        if self.python_Bib_serial == 'usbtmc':      name_KS = self.serial.ask("*IDN?")
        elif self.python_Bib_serial == 'pyvisa':    
            self.serial.write("*IDN?")
            name_KS = self.serial.read()
        logger.info(f'Device identity ({self.name}): {name_KS}')

        self.meas_data = {"VRMS AC Ch.1":[],"VRMS AC Ch.2":[],"VRMS AC Ch.3":[],"VRMS AC Ch.4":[],"VRMS DC Ch.1":[],"VRMS DC Ch.2":[],"VRMS DC Ch.3":[],"VRMS DC Ch.4":[], "Frequency Ch.1":[],"Frequency Ch.2":[],"Frequency Ch.3":[],"Frequency Ch.4":[], 'WaveGen V':[], 'WaveGen f':[]}
        self.channel = {1: self.channel_1_activ, 2: self.channel_2_activ, 3: self.channel_3_activ, 4: self.channel_4_activ}

    def sample(self):
        """Read VRMS form device.

        Returns:
            float: temperature reading.
        """
        data = {"VRMS AC Ch.1": np.nan,"VRMS AC Ch.2":np.nan,"VRMS AC Ch.3":np.nan,"VRMS AC Ch.4":np.nan, "VRMS DC Ch.1": np.nan,"VRMS DC Ch.2":np.nan,"VRMS DC Ch.3":np.nan,"VRMS DC Ch.4":np.nan, "Frequency Ch.1":np.nan,"Frequency Ch.2":np.nan,"Frequency Ch.3":np.nan,"Frequency Ch.4":np.nan, 'WaveGen V':np.nan, 'WaveGen f':np.nan}
        try:
            for n in [1,2,3,4]:
                if self.python_Bib_serial == 'usbtmc': 
                    if self.channel[n]: 
                        data_AC = float(self.serial.ask(":MEAS:VRMS? AC, CHAN" + str(n)))
                        if data_AC <= self.device_NAN_Limit: data[f"VRMS AC Ch.{n}"] = data_AC
                        data_DC = float(self.serial.ask(":MEAS:VRMS? DC, CHAN" + str(n)))
                        if data_DC <= self.device_NAN_Limit: data[f"VRMS DC Ch.{n}"] = data_DC
                        data_Freq = float(self.serial.ask(":MEAS:FREQ? CHAN" + str(n)))
                        if data_Freq <= self.device_NAN_Limit_f: data[f"Frequency Ch.{n}"] = data_Freq
                    if n == 1:
                        data_WGV = float(self.serial.ask(":WGEN:VOLT?"))
                        if data_WGV <= self.device_NAN_Limit: data[f"WaveGen V"] = data_WGV
                        data_WGf = float(self.serial.ask(":WGEN:FREQ?"))
                        if data_WGf <= self.device_NAN_Limit_f: data[f"WaveGen f"] = data_WGf
                elif self.python_Bib_serial == 'pyvisa':
                    if self.channel[n]: 
                        self.serial.write(":MEAS:VRMS? AC, CHAN" + str(n))
                        data_AC = float(self.serial.read())
                        if data_AC <= self.device_NAN_Limit: data[f"VRMS AC Ch.{n}"] = data_AC
                        self.serial.write(":MEAS:VRMS? DC, CHAN" + str(n))
                        data_DC = float(self.serial.read())
                        if data_DC <= self.device_NAN_Limit: data[f"VRMS DC Ch.{n}"] = data_DC
                        self.serial.write(":MEAS:FREQ? CHAN" + str(n))
                        data_Freq = float(self.serial.read())
                        if data_Freq <= self.device_NAN_Limit_f: data[f"Frequency Ch.{n}"] = data_Freq
                    if n == 1:
                        self.serial.write(":WGEN:VOLT?")
                        data_WGV = float(self.serial.read())
                        if data_WGV <= self.device_NAN_Limit: data[f"WaveGen V"] = data_WGV
                        self.serial.write(":WGEN:FREQ?")
                        data_WGf = float(self.serial.read())
                        if data_WGf <= self.device_NAN_Limit_f: data[f"WaveGen f"] = data_WGf
        except Exception as e:
            logger.exception(f"Could not sample Keysight.")
            data = {"VRMS AC Ch.1": np.nan,"VRMS AC Ch.2":np.nan,"VRMS AC Ch.3":np.nan,"VRMS AC Ch.4":np.nan, "VRMS DC Ch.1": np.nan,"VRMS DC Ch.2":np.nan,"VRMS DC Ch.3":np.nan,"VRMS DC Ch.4":np.nan, "Frequency Ch.1":np.nan,"Frequency Ch.2":np.nan,"Frequency Ch.3":np.nan,"Frequency Ch.4":np.nan, 'WaveGen V':np.nan, 'WaveGen f':np.nan}
        
        return data

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        units = "# datetime,s,V,V,V,V,V,V,V,V,Hz,Hz,Hz,Hz,V,Hz,\n"
        header = "time_abs,time_rel,VRMS AC Ch.1,VRMS AC Ch.2,VRMS AC Ch.3,VRMS AC Ch.4,VRMS DC Ch.1,VRMS DC Ch.2,VRMS DC Ch.3,VRMS DC Ch.4,f Ch.1,f Ch.2,f Ch.3,f Ch.4,Wave-Generator V,Wave-Generator f,\n"
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(units)
            f.write(header)
        self.write_nomad_file(directory)

    def write_nomad_file(self, directory="./"):
        """Write .archive.yaml file based on device configuration.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        with open("./multilog/nomad/archive_template_sensor.yml") as f:
            nomad_template = yaml.safe_load(f)
        definitions = nomad_template.pop("definitions")
        data = nomad_template.pop("data")
        sensor_schema_template = nomad_template.pop("sensor_schema_template")
        data.update(
            {
                "data_file": self.filename.split("/")[-1],
            }
        )
        sensor_name_nomad = self.name.replace(" ", "_").replace("-", "_")
        data.update(
            {
                sensor_name_nomad: {
                    # "model": "your_field_here",
                    # "name": sensor_name_nomad,
                    # "sensor_id": sensor_name.split(" ")[0],
                    # "attached_to": sensor_name, # TODO this information is important!
                    # "measured_property": ,
                    # "type": sensor_type,
                    # "notes": "TE_1_K air 155 mm over crucible",
                    # "unit": self.unit[sensor_name],  # TODO
                    "value_timestamp_rel": "#/data/value_timestamp_rel",
                    "value_timestamp_abs": "#/data/value_timestamp_abs",
                }
            }
        )
        if "comment" in self.config:
            data[sensor_name_nomad].update({"comment": self.config["comment"]})
        sensor_schema = deepcopy(sensor_schema_template)
        sensor_schema["section"]["quantities"]["value_log"]["m_annotations"]["tabular"][
            "name"
        ] = "Temperature"
        definitions["sections"]["Sensors_list"]["sub_sections"].update(
            {sensor_name_nomad: sensor_schema}
        )
        nomad_dict = {
            "definitions": definitions,
            "data": data,
        }
        with open(f"{directory}/{self.name}.archive.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(nomad_dict, f, sort_keys=False)

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
        self.meas_data["VRMS AC Ch.1"].append(sampling["VRMS AC Ch.1"])
        self.meas_data["VRMS AC Ch.2"].append(sampling["VRMS AC Ch.2"])
        self.meas_data["VRMS AC Ch.3"].append(sampling["VRMS AC Ch.3"])
        self.meas_data["VRMS AC Ch.4"].append(sampling["VRMS AC Ch.4"])
        self.meas_data["VRMS DC Ch.1"].append(sampling["VRMS DC Ch.1"])
        self.meas_data["VRMS DC Ch.2"].append(sampling["VRMS DC Ch.2"])
        self.meas_data["VRMS DC Ch.3"].append(sampling["VRMS DC Ch.3"])
        self.meas_data["VRMS DC Ch.4"].append(sampling["VRMS DC Ch.4"])
        self.meas_data["Frequency Ch.1"].append(sampling["Frequency Ch.1"])
        self.meas_data["Frequency Ch.2"].append(sampling["Frequency Ch.2"])
        self.meas_data["Frequency Ch.3"].append(sampling["Frequency Ch.3"])
        self.meas_data["Frequency Ch.4"].append(sampling["Frequency Ch.4"])
        self.meas_data["WaveGen V"].append(sampling["WaveGen V"])
        self.meas_data["WaveGen f"].append(sampling["WaveGen f"])
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{sampling['VRMS AC Ch.1']},{sampling['VRMS AC Ch.2']},{sampling['VRMS AC Ch.3']},{sampling['VRMS AC Ch.4']},{sampling['VRMS DC Ch.1']},{sampling['VRMS DC Ch.2']},{sampling['VRMS DC Ch.3']},{sampling['VRMS DC Ch.4']},{sampling['Frequency Ch.1']},{sampling['Frequency Ch.2']},{sampling['Frequency Ch.3']},{sampling['Frequency Ch.4']},{sampling['WaveGen V']},{sampling['WaveGen f']},\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)
