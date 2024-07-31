import logging
import datetime
import socket
import json
import yaml
from copy import deepcopy
import time
import numpy as np

logger = logging.getLogger(__name__)

class Vifcon_achsen:
    def __init__(self, config, name="vifcon"):
        """Prepare sampling.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): device name.
        """

        logger.info(f"Initializing vifcon device '{name}'")
        
        self.config = config
        self.name = name
        self.vifconIP = config["IP"]

        # lists
        self.hub = []
        self.rot = []
        self.pi  = []
        self.connectionList = []
        sleepTime = 0.1 # pause needed between conections, otherwise connection will fail!

        try:
            for axis in config["Axis"]:
                axisName = config["Axis"][axis]["Name"] # get name
                
                if "Hub" in axisName.capitalize():
                    try:
                        self.hub.append(axis) # append to hub liste

                        # TCP conection:
                        s = socket.socket()
                        s.connect((self.vifconIP,  config["Axis"][axis]["Port"]))
                        self.connectionList.append(s)
                        logger.debug(f"{axisName} connected to VIFCON")
                        time.sleep(sleepTime)
                    except Exception as e:
                        logger.exception(f"Connection to {self.name}: {self.axisName} not possible.")
                        time.sleep(sleepTime)
                        
                if "Rot" in axisName.capitalize():
                    try:
                        self.rot.append(axis) # append to rot liste

                        # TCP conection:
                        s = socket.socket()
                        s.connect((self.vifconIP,  config["Axis"][axis]["Port"]))
                        self.connectionList.append(s)
                        logger.debug(f"{axisName} connected to VIFCON")
                        time.sleep(sleepTime)
                    except Exception as e:
                        logger.exception(f"Connection to {self.name}: {self.axisName} not possible.")
                        time.sleep(sleepTime)
                        
                if "Pi" in axisName.capitalize():
                    try:
                        self.pi.append(axis) # append to pi liste
                        
                        # TCP conection:
                        s = socket.socket() 
                        s.connect((self.vifconIP,  config["Axis"][axis]["Port"])) 
                        self.connectionList.append(s)
                        logger.debug(f"{axisName} connected to VIFCON")
                        time.sleep(sleepTime)
                    except Exception as e:
                        logger.exception(f"Connection to {self.name}: {self.axisName} not possible.")
                        time.sleep(sleepTime)
        except Exception as e:
            logger.exception(f"{self.name}: has no Axis definded.")
            
                    
        # Build measData
        self.meas_data = {}
        for axis in self.hub:
            self.meas_data.update({f"{axis}": {"IWs": [], "IWv": [], "SWv": [], "SWs": [], "oGs": [], "uGs": []}})

        for axis in self.rot:
            self.meas_data.update({f"{axis}": {"IWv": [], "IWw": [], "SWv": []}})

        for axis in self.pi:
            self.meas_data.update({f"{axis}": {"IWs": [], "IWv": []}})

    def sample(self):
        # send trigger
        i = 0
        jsonList = []
        
        for axis in self.hub:
            try:
                self.connectionList[i].send(bytes(f"{axis}", 'UTF-8'))
                received = self.connectionList[i].recv(1024)
                jsonList.append(json.loads(received.decode("utf-8")))
            except Exception as e:
                logger.exception(f"Could not sample {self.name}.")
                jsonList.append({"IWs": np.nan, "IWv": np.nan, "SWv": np.nan, "SWs": np.nan, "oGs": np.nan, "uGs": np.nan})
            i=i+1
        for axis in self.rot:
            try:
                self.connectionList[i].send(bytes(f"{axis}", 'UTF-8'))
                received = self.connectionList[i].recv(1024)
                jsonList.append(json.loads(received.decode("utf-8")))
            except Exception as e:
                logger.exception(f"Could not sample {self.name}.")
                jsonList.append({"IWv": np.nan, "IWw": np.nan, "SWv": np.nan})
            i=i+1
        for axis in self.pi:
            try:
                self.connectionList[i].send(bytes(f"{axis}", 'UTF-8'))
                received = self.connectionList[i].recv(1024)
                jsonList.append(json.loads(received.decode("utf-8")))
            except Exception as e:
                logger.exception(f"Could not sample {self.name}.")
                jsonList.append({"IWs": np.nan, "IWv": np.nan})
            i=i+1
        
        # Build data
        data = {}
        i = 0
        for axis in self.hub:
            data.update({f"{axis}" : jsonList[i]})
            i = i + 1
        
        for axis in self.rot:
            data.update({f"{axis}" : jsonList[i]})
            i = i + 1
            
        for axis in self.pi:
            data.update({f"{axis}" : jsonList[i]})
            data[f"{axis}"]["IWv"] = data[f"{axis}"]["IWv"]/60 # mm/s in mm/min umrechnen
            i = i + 1
        return data

    def save_measurement(self, time_abs, time_rel, sampling):
        """Write measurement data to file.

        Args:
            time_abs (datetime): measurement timestamp.
            time_rel (float): relative time of measurement.
            sampling (dict): sampling data, as returned from sample()
        """
        timediff = (
            datetime.datetime.now(datetime.timezone.utc).astimezone() - time_abs
        ).total_seconds()
        if timediff > 1:
            logger.warning(
                f"{self.name} save_measurement: time difference between event and saving of {timediff} seconds for samplint timestep {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')} - {time_rel}"
            )

        line = f"""{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel}"""
        for axis in self.hub:
            self.meas_data[f"{axis}"]["IWs"].append(sampling[f"{axis}"]["IWs"])
            self.meas_data[f"{axis}"]["SWs"].append(sampling[f"{axis}"]["SWs"])
            self.meas_data[f"{axis}"]["oGs"].append(sampling[f"{axis}"]["oGs"])
            self.meas_data[f"{axis}"]["uGs"].append(sampling[f"{axis}"]["uGs"])
            self.meas_data[f"{axis}"]["IWv"].append(sampling[f"{axis}"]["IWv"])
            self.meas_data[f"{axis}"]["SWv"].append(sampling[f"{axis}"]["SWv"])
            
            line = line + ',' + str(sampling[f"{axis}"]["IWs"])
            line = line + ',' + str(sampling[f"{axis}"]["SWs"])
            line = line + ',' + str(sampling[f"{axis}"]["oGs"])
            line = line + ',' + str(sampling[f"{axis}"]["uGs"])
            line = line + ',' + str(sampling[f"{axis}"]["IWv"])
            line = line + ',' + str(sampling[f"{axis}"]["SWv"])
            
        for axis in self.rot:
            self.meas_data[f"{axis}"]["IWw"].append(sampling[f"{axis}"]["IWw"])
            self.meas_data[f"{axis}"]["IWv"].append(sampling[f"{axis}"]["IWv"])
            self.meas_data[f"{axis}"]["SWv"].append(sampling[f"{axis}"]["SWv"])

            line = line + ',' + str(sampling[f"{axis}"]["IWw"])
            line = line + ',' + str(sampling[f"{axis}"]["IWv"])
            line = line + ',' + str(sampling[f"{axis}"]["SWv"])
        
        for axis in self.pi:
            self.meas_data[f"{axis}"]["IWs"].append(sampling[f"{axis}"]["IWs"])
            self.meas_data[f"{axis}"]["IWv"].append(sampling[f"{axis}"]["IWv"])

            line = line + ',' + str(sampling[f"{axis}"]["IWs"])
            line = line + ',' + str(sampling[f"{axis}"]["IWv"])

        line = line + ("\n")

        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        units = "# datetime,s,mm"
        header = "time_abs,time_rel"

        for axis in self.hub:
            units = units + ",mm,mm,mm,mm,mm/min,mm/min"
            header = header + f",{axis}IWs,{axis}SWs,{axis}OGs,{axis}UGs,{axis}IWv,{axis}SWv"

        for axis in self.rot:
            units = units + ",deg,deg/min,deg/min"
            header = header + f",{axis}IWw,{axis}IWv,{axis}SWv"

        for axis in self.pi:
            units = units + ",mm,mm/min"
            header = header + f",{axis}IWs,{axis}IWv"
            
        units  = units  + "\n"
        header = header + "\n"
        
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(units)
            f.write(header)
        self.write_nomad_file(directory)


    def write_nomad_file(self, directory="./"):
        # Write .archive.yaml file based on device configuration.
        #
        # Args:
        #    directory (str, optional): Output directory. Defaults to "./".

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
        for sensor_name in self.meas_data:
            sensor_name_nomad = sensor_name.replace(" ", "_").replace("-", "_")
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
            sensor_schema["section"]["quantities"]["value_log"]["m_annotations"][
                "tabular"
            ]["name"] = sensor_name
            definitions["sections"]["Sensors_list"]["sub_sections"].update(
                {sensor_name_nomad: sensor_schema}
            )
        nomad_dict = {
            "definitions": definitions,
            "data": data,
        }
        with open(f"{directory}/{self.name}.archive.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(nomad_dict, f, sort_keys=False)

    # needed for displaying the data
    def getAxis(self):
        return self.hub, self.rot, self.pi
        
