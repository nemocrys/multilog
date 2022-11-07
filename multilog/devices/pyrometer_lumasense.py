from copy import deepcopy
import datetime
import logging
import numpy as np
from serial import Serial, SerialException
import yaml

logger = logging.getLogger(__name__)


class SerialMock:
    """This class is used to mock a serial interface for debugging purposes."""

    def write(self, _):
        pass

    def readline(self):
        return "".encode()


class PyrometerLumasense:
    """Lumasense pyrometer, e.g. IGA-6-23 or IGAR-6-adv."""

    def __init__(self, config, name="PyrometerLumasense"):
        """Setup serial interface, configure device.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
        """
        logger.info(f"Initializing PyrometerLumasense device '{name}'")
        self.device_id = config["device-id"]
        self.name = name
        self.t90_dict = config["t90-dict"]
        try:
            self.serial = Serial(**config["serial-interface"])
        except SerialException as e:
            logger.exception(f"Connection to {self.name} not possible.")
            self.serial = SerialMock()
        if type(self.serial) != SerialMock:
            self.set_emissivity(config["emissivity"])
            self.set_transmissivity(config["transmissivity"])
            self.set_t90(config["t90"])
        self.meas_data = []

    def _get_ok(self):
        """Check if command was accepted."""
        assert self.serial.readline().decode().strip() == "ok"

    def _get_float(self):
        """Read floatingpoint value."""
        string_val = self.serial.readline().decode().strip()
        return float(f"{string_val[:-1]}.{string_val[-1:]}")

    @property
    def focus(self):
        """Get focuspoint."""
        cmd = f"{self.device_id}df\r"
        self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    @property
    def intrument_id(self):
        """Get the instrument id."""
        if type(self.serial) == SerialMock:
            return -1
        cmd = f"{self.device_id}na\r"
        self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    @property
    def emissivity(self):
        """Read the current emissivity."""
        if type(self.serial) == SerialMock:
            return -1
        cmd = f"{self.device_id}em\r"
        self.serial.write(cmd.encode())
        return self._get_float()

    @property
    def transmissivity(self):
        """Read the current transmissivity."""
        if type(self.serial) == SerialMock:
            return -1
        cmd = f"{self.device_id}et\r"
        self.serial.write(cmd.encode())
        return self._get_float()

    @property
    def t90(self):
        """Reat the current t90 value."""
        if type(self.serial) == SerialMock:
            return -1
        cmd = f"{self.device_id}ez\r"
        self.serial.write(cmd.encode())
        idx = int(self.serial.readline().decode().strip())
        t90_dict_inverted = {v: k for k, v in self.t90_dict.items()}
        return t90_dict_inverted[idx]

    def set_emissivity(self, emissivity):
        """Set emissivity and check if it was accepted."""
        logger.info(f"{self.name} - setting emissivity {emissivity}")
        cmd = f"{self.device_id}em{emissivity*100:05.1f}\r".replace(".", "")
        self.serial.write(cmd.encode())
        self._get_ok()
        assert self.emissivity == emissivity * 100

    def set_transmissivity(self, transmissivity):
        """Set transmissivity and check if it was accepted."""
        logger.info(f"{self.name} - setting transmissivity {transmissivity}")
        cmd = f"{self.device_id}et{transmissivity*100:05.1f}\r".replace(".", "")
        self.serial.write(cmd.encode())
        self._get_ok()
        assert self.transmissivity == transmissivity * 100

    def set_t90(self, t90):
        """Set t90 and check if it was accepted."""
        logger.info(f"{self.name} - setting t90 {t90}")
        cmd = f"{self.device_id}ez{self.t90_dict[t90]}\r"
        self.serial.write(cmd.encode())
        self._get_ok()
        assert self.t90 == t90

    def sample(self):
        """Read temperature form device.

        Returns:
            float: temperature reading.
        """
        try:
            cmd = f"{self.device_id}ms\r"
            self.serial.write(cmd.encode())
            val = self._get_float()
        except Exception as e:
            logger.exception(f"Could not sample PyrometerLumasense.")
            val = np.nan
        return val

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
        self.write_nomad_files(directory)

    def write_nomad_files(self, directory="./"):
        """Write .archive.yaml file based on device configuration.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        with open("./multilog/nomad/archive_template.yml") as f:
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
                    "name": sensor_name_nomad,
                    # "sensor_id": sensor_name.split(" ")[0],
                    # "attached_to": sensor_name, # TODO this information is important!
                    # "measured_property": ,
                    # "type": sensor_type,
                    # "notes": "TE_1_K air 155 mm over crucible",
                    # "unit": self.unit[sensor_name],  # TODO
                    "emissivity": self.emissivity,
                    "transmissivity": self.transmissivity,
                    "t90": self.t90,
                    "value_timestamp_rel": "#/data/value_timestamp_rel",
                    "value_timestamp_abs": "#/data/value_timestamp_abs",
                }
            }
        )
        sensor_schema = deepcopy(sensor_schema_template)
        sensor_schema["section"]["quantities"]["value_log"]["m_annotations"][
            "tabular"
        ]["name"] = "Temperature"
        definitions["sections"]["Sensors_list"]["sub_sections"].update(
            {sensor_name_nomad: sensor_schema}
        )
        definitions["sections"]["Sensors_list"]["m_annotations"]["plot"].append(
            {
                "label": f"{sensor_name_nomad} over time",
                "x": "value_timestamp_rel",
                "y": [f"{sensor_name_nomad}/value_log"],
            }
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
        self.meas_data.append(sampling)
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{sampling},\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)
