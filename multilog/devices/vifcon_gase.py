import logging
import datetime
import socket
import json
import yaml
from copy import deepcopy
import numpy as np

logger = logging.getLogger(__name__)

class Vifcon_gase:
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
        self.vifconPort = config["Port"]
        
        # TCP STUFF
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.s.connect((self.vifconIP, self.vifconPort))
            logger.info(f"{self.name} connected to VIFCON")
        except Exception as e:
            logger.exception(f"Connection to {self.name} not possible.")

        self.meas_data = {"MFC24": [], "MFC25": [], "MFC26": [], "MFC27": [], "DM21": [], "PP21": [], "PP22": [], "PP22I": []}

    def sample(self):
        # send trigger
        try:
            self.s.send(bytes(self.name, 'UTF-8'))
            received = self.s.recv(1024)
            received = received.decode("utf-8")
            data = json.loads(received)
        except Exception as e:
            logger.exception(f"Could not sample {self.name}.")
            data = {"MFC24": np.nan, "MFC25": np.nan, "MFC26": np.nan, "MFC27": np.nan, "DM21": np.nan, "PP21": np.nan, "PP22": np.nan, "PP22I": np.nan}
        
        # change pressure data to np.nan if value is to low
        if data["PP21"] <= 1e-5: data["PP21"] = np.nan
        if data["PP22"] <= 1e-5: data["PP22"] = np.nan
        if data["DM21"] <= 1e-5: data["DM21"] = np.nan
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
        # Format pressure data as scientific notation
        dm21Formated = "{:.2E}".format(sampling["DM21"])
        pp21Formated = "{:.2E}".format(sampling["PP21"])
        pp22Formated = "{:.2E}".format(sampling["PP22"])

        self.meas_data["MFC24"].append(sampling["MFC24"])
        self.meas_data["MFC25"].append(sampling["MFC25"])
        self.meas_data["MFC26"].append(sampling["MFC26"])
        self.meas_data["MFC27"].append(sampling["MFC27"])
        self.meas_data["DM21"].append(dm21Formated)
        self.meas_data["PP21"].append(pp21Formated)
        self.meas_data["PP22"].append(pp22Formated)
        self.meas_data["PP22I"].append(sampling["PP22I"])
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{sampling['MFC24']},{sampling['MFC25']},{sampling['MFC26']},{sampling['MFC27']},{dm21Formated},{pp21Formated},{pp22Formated},{sampling['PP22I']},\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        units = "# datetime,s,ml/min,ml/min,ml/min,ml/min,mbar,mbar,mbar,%\n"
        header = "time_abs,time_rel,MFC24,MFC25,MFC26,MFC27,DM21,PP21,PP22,PP22I\n"
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
