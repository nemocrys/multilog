"""This module contains a class for each device implementing
device configuration, communication and saving of measurement data.

Each device must implement the following functions:
- init_output(self, directory: str) -> None
- sample(self) -> Any
- save_measurement(self, time_abs: float, time_rel: datetime, sampling: Any) -> None
"""

from copy import deepcopy
import datetime
import logging
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
from serial import Serial, SerialException
import subprocess
import traceback
import yaml

logger = logging.getLogger(__name__)

from .discord_bot import send_message

# device-specific imports
# required by IfmFlowmeter
try:
    import requests
except Exception as e:
    logger.warning("Could not import requests.", exc_info=True)
# required by BaslerCamera
try:
    from pypylon import pylon
except Exception as e:
    logger.warning("Could not import pypylon.", exc_info=True)
# required by BaslerCamera
try:
    from PIL import Image
except Exception as e:
    logger.warning("Could not import PIL.", exc_info=True)
# required by OptrisIP640
try:
    from mpl_toolkits.axes_grid1 import make_axes_locatable
except Exception as e:
    logger.warning("Could not import mpl_toolkits.", exc_info=True)
# required by OptrisIP640
try:
    from .pyOptris import direct_binding as optris
except Exception as e:
    logger.warning(f"Could not import pyOtris", exc_info=True)


class SerialMock:
    """This class is used to mock a serial interface for debugging purposes."""

    def write(self, _):
        pass

    def readline(self):
        return "".encode()


class Daq6510:
    """Keythley multimeter DAQ6510. Implementation bases on v1 of
    multilog and shall be refactored in future."""

    def __init__(self, config, name="Daq6510"):
        """Setup serial interface, configure device and prepare sampling.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
        """
        logger.info(f"Initializing Daq6510 device '{name}'")
        self.config = config
        self.name = name
        try:
            self.serial = Serial(**config["serial-interface"])
        except SerialException as e:
            logger.exception(f"Connection to {self.name} not possible.")
            self.serial = SerialMock()
        self.reset()
        # bring the data from config into multilog v1 compatible structure
        self.nb_reading_values = len(config["channels"])
        self.reading_str = "(@"

        self.ch_list_tc = []
        self.ch_list_pt100 = []
        self.ch_list_pt1000 = []
        self.ch_list_dcv = []
        self.ch_list_acv = []

        self.ch_str_tc = "(@"
        self.ch_str_tc_k = "(@"
        self.ch_str_tc_j = "(@"
        self.ch_str_pt_100 = "(@"
        self.ch_str_pt_1000 = "(@"
        self.ch_str_dcv = "(@"
        self.ch_str_acv = "(@"

        self.nb_tc_k = 0
        self.nb_tc_j = 0
        self.nb_pt100 = 0
        self.nb_pt1000 = 0
        self.nb_dcv = 0
        self.nb_acv = 0

        for channel in config["channels"]:
            self.reading_str += f"{channel},"
            sensor_type = config["channels"][channel]["type"].lower()
            if sensor_type == "temperature":
                subtype = config["channels"][channel]["sensor-id"].split("_")[0].lower()
                if subtype == "te":  # thermo couple
                    self.ch_list_tc.append(channel)
                    self.ch_str_tc += f"{channel},"
                    tc_type = (
                        config["channels"][channel]["sensor-id"].split("_")[-1].lower()
                    )
                    if tc_type == "k":
                        self.nb_tc_k += 1
                        self.ch_str_tc_k += f"{channel},"
                    if tc_type == "j":
                        self.nb_tc_j += 1
                        self.ch_str_tc_j += f"{channel},"
                if subtype == "pt-100":
                    self.ch_list_pt100.append(channel)
                    self.nb_pt100 += 1
                    self.ch_str_pt_100 += f"{channel},"
                if subtype == "pt-1000":
                    self.ch_list_pt1000.append(channel)
                    self.nb_pt1000 += 1
                    self.ch_str_pt_1000 += f"{channel},"
            elif sensor_type == "dcv":
                self.ch_list_dcv.append(channel)
                self.nb_dcv += 1
                self.ch_str_dcv += f"{channel},"
            elif sensor_type == "acv":
                self.ch_list_acv.append(channel)
                self.nb_acv += 1
                self.ch_str_acv += f"{channel},"
            else:
                raise ValueError(
                    f"Unknown sensor type {sensor_type} at channel {channel}."
                )

        self.reading_str = self.reading_str[:-1] + ")"
        self.ch_str_tc = self.ch_str_tc[:-1] + ")"
        self.ch_str_tc_k = self.ch_str_tc_k[:-1] + ")"
        self.ch_str_tc_j = self.ch_str_tc_j[:-1] + ")"
        self.ch_str_pt_100 = self.ch_str_pt_100[:-1] + ")"
        self.ch_str_pt_1000 = self.ch_str_pt_1000[:-1] + ")"
        self.ch_str_dcv = self.ch_str_dcv[:-1] + ")"
        self.ch_str_acv = self.ch_str_acv[:-1] + ")"

        if config["settings"]["lsync"]:
            lsync = "ON"
        else:
            lsync = "OFF"
        if config["settings"]["ocom"]:
            ocom = "ON"
        else:
            ocom = "OFF"
        if config["settings"]["azer"]:
            azer = "ON"
        else:
            azer = "OFF"
        if config["settings"]["adel"]:
            adel = "ON"
        else:
            adel = "OFF"

        cmds = [
            ":SYSTEM:CLEAR\n",
            "FORM:DATA ASCII\n",
        ]
        if self.nb_tc_k + self.nb_tc_j > 0:  # if there are thermo couples
            cmds.append(f'FUNC "TEMP", {self.ch_str_tc}\n')
            cmds.append(f"TEMP:TRAN TC, {self.ch_str_tc}\n")
            if self.nb_tc_k > 0:
                cmds.append(f"TEMP:TC:TYPE K, {self.ch_str_tc_k}\n")
            if self.nb_tc_j > 0:
                cmds.append(f"TEMP:TC:TYPE J, {self.ch_str_tc_j}\n")
            cmds.append(f"TEMP:UNIT CELS, {self.ch_str_tc}\n")
            if config["settings"]["internal-cold-junction"]:
                cmds.append(f"TEMP:TC:RJUN:RSEL INT, {self.ch_str_tc}\n")
            else:
                cmds.append(f"TEMP:TC:RJUN:RSEL SIM, {self.ch_str_tc}\n")
                cmds.append(f"TEMP:TC:RJUN:SIM 0, {self.ch_str_tc}\n")
            cmds.append(f"TEMP:AVER OFF, {self.ch_str_tc}\n")
            cmds.append(f"TEMP:LINE:SYNC {lsync}, {self.ch_str_tc}\n")
            cmds.append(f"TEMP:OCOM {ocom}, {self.ch_str_tc}\n")
            cmds.append(f"TEMP:AZER {azer}, {self.ch_str_tc}\n")
            cmds.append(f"TEMP:DEL:AUTO {adel}, {self.ch_str_tc}\n")
            for channel in self.ch_list_tc:
                cmds.append(f'TEMP:NPLC {config["settings"]["nplc"]}, (@{channel})\n')
        if self.nb_pt100 > 0:
            cmds.append(f'FUNC "TEMP", {self.ch_str_pt_100}\n')
            cmds.append(f"TEMP:TRAN FRTD, {self.ch_str_pt_100}\n")
            cmds.append(f"TEMP:RTD:FOUR PT100, {self.ch_str_pt_100}\n")
            cmds.append(f"TEMP:LINE:SYNC {lsync}, {self.ch_str_pt_100}\n")
            cmds.append(f"TEMP:OCOM {ocom}, {self.ch_str_pt_100}\n")
            cmds.append(f"TEMP:AZER {azer}, {self.ch_str_pt_100}\n")
            cmds.append(f"TEMP:DEL:AUTO {adel}, {self.ch_str_pt_100}\n")
            cmds.append(f"TEMP:AVER OFF, {self.ch_str_pt_100}\n")
            for channel in self.ch_list_pt100:
                cmds.append(f'TEMP:NPLC {config["settings"]["nplc"]}, (@{channel})\n')
        if self.nb_pt1000 > 0:  # PT1000 temperature calculated inside DAQ
            cmds.append(f'FUNC "TEMP", {self.ch_str_pt_1000}\n')
            cmds.append(f"TEMP:TRAN FRTD, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:RTD:FOUR USER, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:RTD:ALPH 0.00385055, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:RTD:BETA 0.10863, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:RTD:DELT 1.4999, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:RTD:ZERO 1000, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:LINE:SYNC {lsync}, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:OCOM {ocom}, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:AZER {azer}, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:DEL:AUTO {adel}, {self.ch_str_pt_1000}\n")
            cmds.append(f"TEMP:AVER OFF, {self.ch_str_pt_1000}\n")
            for channel in self.ch_list_pt1000:
                cmds.append(f'TEMP:NPLC {config["settings"]["nplc"]}, (@{channel})\n')
        if self.nb_dcv > 0:
            cmds.append(f'FUNC "VOLT:DC", {self.ch_str_dcv}\n')
            cmds.append(f"VOLT:LINE:SYNC {lsync}, {self.ch_str_dcv}\n")
            cmds.append(f"VOLT:AZER {azer}, {self.ch_str_dcv}\n")
            cmds.append(f"VOLT:DEL:AUTO {adel}, {self.ch_str_dcv}\n")
            cmds.append(f"VOLT:AVER OFF, {self.ch_str_dcv}\n")
            for channel in self.ch_list_dcv:
                cmds.append(f'VOLT:NPLC {config["settings"]["nplc"]}, (@{channel})\n')
                if "range" in config["channels"][channel]:
                    cmds.append(
                        f'VOLT:RANG {config["channels"][channel]["range"]}, (@{channel})\n'
                    )
                else:
                    cmds.append(f"VOLT:RANG:AUTO ON, (@{channel})\n")
        if self.nb_acv > 0:
            cmds.append(f'FUNC "VOLT:AC", {self.ch_str_acv}\n')
            cmds.append(f"VOLT:AC:AVER OFF, {self.ch_str_acv}\n")
            cmds.append(f"VOLT:AC:DEL:AUTO {adel}, {self.ch_str_acv}\n")
            for channel in self.ch_list_acv:
                if "range" in config["channels"][channel]:
                    cmds.append(
                        f'VOLT:AC:RANG {config["channels"][channel]["range"]}, (@{channel})\n'
                    )
                else:
                    cmds.append(f"VOLT:AC:RANG:AUTO ON, (@{channel})\n")
            # only signals with frequency greater than the detector bandwidth are measured
            # detectors bandwith: 3, 30 or 300 Hz, default = 3
            cmds.append(f"VOLT:AC:DET:BAND 300, {self.ch_str_acv}\n")
        cmds.append("DISP:CLE\n")
        cmds.append("DISP:LIGH:STAT ON50\n")
        cmds.append('DISP:USER1:TEXT "ready to start ..."\n')

        for cmd in cmds:
            self.serial.write(cmd.encode())

        # container for measurement data, allocation of channel_id and name
        self.meas_data = {}
        self.channel_id_names = {}
        for channel in config["channels"]:
            if "position" in config["channels"][channel]:
                name = f'{config["channels"][channel]["sensor-id"]} {config["channels"][channel]["position"]}'
            else:
                name = f'{config["channels"][channel]["sensor-id"]}'
            name = name.replace(",", "")
            self.meas_data.update({name: []})
            self.channel_id_names.update({channel: name})

        # unit conversion (for dcv and acv channels)
        self.conversion_factor = {}
        self.unit = {}
        for channel in config["channels"]:
            type = config["channels"][channel]["type"].lower()
            name = self.channel_id_names[channel]
            if type == "temperature":
                self.unit.update({name: "°C"})
                self.conversion_factor.update({name: 1})
            else:  # acv, dcv
                if "unit" in config["channels"][channel]:
                    self.unit.update({name: config["channels"][channel]["unit"]})
                else:
                    self.unit.update({name: "V"})
                if "factor" in config["channels"][channel]:
                    self.conversion_factor.update(
                        {name: config["channels"][channel]["factor"]}
                    )
                else:
                    self.conversion_factor.update({name: 1})

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        units = "# datetime,s,"
        header = "time_abs,time_rel,"
        for sensor in self.meas_data:
            units += f"{self.unit[sensor].replace('°', 'DEG ')},"
            header += f"{sensor},"
        units += "\n"
        header += "\n"
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
        for channel in self.channel_id_names:
            sensor_name = self.channel_id_names[channel]
            sensor_name_nomad = sensor_name.replace(" ", "_").replace("-", "_")
            data.update(
                {
                    sensor_name_nomad: {
                        # "model": "your_field_here",
                        "name": sensor_name_nomad,
                        "sensor_id": sensor_name.split(" ")[0],
                        "attached_to": " ".join(sensor_name.split(" ")[1:]),
                        "measured_property": self.config["channels"][channel]["type"],
                        "type": sensor_name.split("_")[0].split(" ")[0],
                        # "notes": "TE_1_K air 155 mm over crucible",
                        # "unit": self.unit[sensor_name],  # TODO
                        # "channel": channel,  # TODO
                        "value_timestamp_rel": "#/data/value_timestamp_rel",
                        "value_timestamp_abs": "#/data/value_timestamp_abs",
                    }
                }
            )
            sensor_schema = deepcopy(sensor_schema_template)
            sensor_schema["section"]["quantities"]["value_log"]["m_annotations"][
                "tabular"
            ]["name"] = sensor_name
            definitions["sections"]["Sensors_list"]["sub_sections"].update(
                {sensor_name_nomad: sensor_schema}
            )
            definitions["sections"]["Sensors_list"]["m_annotations"]["plot"].append(
                {
                    "label": f"{sensor_name} over time",
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
            sampling (dict): sampling data, as returned from sample()
        """
        timediff = (
            datetime.datetime.now(datetime.timezone.utc).astimezone() - time_abs
        ).total_seconds()
        if timediff > 1:
            logger.warning(
                f"{self.name} save_measurement: time difference between event and saving of {timediff} seconds for samplint timestep {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')} - {time_rel}"
            )
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},"
        for sensor in self.meas_data:
            self.meas_data[sensor].append(sampling[sensor])
            line += f"{sampling[sensor]},"
        line += "\n"
        with open(self.filename, "a") as f:
            f.write(line)

    @property
    def device_id(self):
        """Get the device ID."""
        cmd = "*IDN?\n"
        self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    @property
    def card1_id(self):
        """Get the ID of Card #1."""
        cmd = "SYST:CARD1:IDN?\n"
        self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    @property
    def card2_id(self):
        """Get the ID of Card #2."""
        cmd = "SYST:CARD2:IDN?\n"
        self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    def set_display_message(self, message="hello world"):
        """Set a message on the display."""
        cmd = f'DISP:USER1:TEXT "{message}"\n'
        self.serial.write(cmd.encode())

    def reset(self):
        """Reset device to factory default."""
        logger.info(f"{self.name} - resetting device")
        cmd = "*RST\n"
        self.serial.write(cmd.encode())

    def read(self):
        """Read out all channels.

        Returns:
            str: measurement data
        """
        cmds = [
            "TRAC:CLE\n",
            "TRAC:POIN 100\n",
            f"ROUT:SCAN:CRE {self.reading_str}\n",
            "ROUT:SCAN:COUN:SCAN 1\n",
            "INIT\n",
            "*WAI\n",
            f'TRAC:DATA? 1,{self.nb_reading_values},"defbuffer1", CHAN, READ\n',
        ]
        for cmd in cmds:
            self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    def sample(self):
        """Read sampling form device and convert values to specified format.

        Returns:
            dict: {sensor name: measurement value}
        """
        data = self.read().split(",")  # = ['channel', 'value', 'channel', 'value', ...]

        if len(data) != 2 * self.nb_reading_values:  # there is an error in the sampling
            logging.error(
                f"Sampling of Daq6510 '{self.name}' failed. Expected {2* self.nb_reading_values} values but got {data}"
            )
            return {v: np.nan for _, v in self.channel_id_names.items()}
        sampling = {}
        for i in range(int(len(data) / 2)):
            channel = int(data[2 * i])
            sensor_name = self.channel_id_names[channel]
            measurement_value = (
                float(data[2 * i + 1]) * self.conversion_factor[sensor_name]
            )
            sampling.update({sensor_name: measurement_value})
        return sampling


class IfmFlowmeter:
    def __init__(self, config, name="IfmFlowmeter"):
        """Prepare sampling.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): device name.
        """
        logger.info(f"Initializing IfmFlowmeter device '{name}'")
        self.config = config
        self.name = name
        self.ip = config["IP"]
        self.ports = config["ports"]
        self.meas_data = {"Temperature": {}, "Flow": {}}
        for port_id in self.ports:
            name = self.ports[port_id]["name"]
            self.meas_data["Temperature"].update({name: []})
            self.meas_data["Flow"].update({name: []})
        self.last_sampling = {"Temperature": {}, "Flow": {}}
        if "flow-balance" in config:
            self.inflow_sensors = config["flow-balance"]["inflow"]
            self.outflow_sensors = config["flow-balance"]["outflow"]
            self.tolerance = config["flow-balance"]["tolerance"]
            for sensor in self.inflow_sensors + self.outflow_sensors:
                self.last_sampling["Flow"].update({sensor: 0})

    def sample(self):
        """Read sampling form device and convert values to readable format.

        Returns:
            dict: {sensor name: measurement value}
        """
        sampling = {"Temperature": {}, "Flow": {}}
        for port in self.ports:
            try:
                name = self.ports[port]["name"]
                sensor_type = self.ports[port]["type"]
                r = requests.get(
                    f"http://{self.ip}/iolinkmaster/port[{port}]/iolinkdevice/pdin/getdata"
                )
                data = r.json()
                data_hex = data["data"]["value"]
                l = len(data_hex)
                if sensor_type == "SM-8020":
                    data_hex_t = data_hex[l - 8 : l - 4]
                    data_hex_f = data_hex[l - 16 : l - 12]
                    data_dec_t = 0.01 * int(data_hex_t, 16)
                    data_dec_f = 0.0166667 * int(data_hex_f, 16)
                elif sensor_type == "SV-4200":
                    data_hex_t = data_hex[l - 4 :]
                    data_hex_f = data_hex[l - 8 : l - 4]
                    data_dec_t = 0.1 * int(data_hex_t, 16) / 4
                    data_dec_f = 0.1 * int(data_hex_f, 16)
                elif sensor_type == "SBG-233":
                    data_hex_t = data_hex[l - 4 :]
                    data_hex_f = data_hex[l - 8 : l - 4]
                    data_dec_t = 1.0 * int(data_hex_t, 16) / 4
                    data_dec_f = 0.1 * int(data_hex_f, 16)
            except Exception as e:
                logger.exception(f"Could not sample IfmFlowmeter port '{name}'.")
                data_dec_t = np.nan
                data_dec_f = np.nan
            sampling["Temperature"].update({name: data_dec_t})
            sampling["Flow"].update({name: data_dec_f})
        self.last_sampling = deepcopy(sampling)
        return sampling

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
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},"
        for sensor in self.meas_data["Flow"]:
            self.meas_data["Flow"][sensor].append(sampling["Flow"][sensor])
            line += f"{sampling['Flow'][sensor]},"
        for sensor in self.meas_data["Temperature"]:
            self.meas_data["Temperature"][sensor].append(
                sampling["Temperature"][sensor]
            )
            line += f"{sampling['Temperature'][sensor]},"
        line += "\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        units = "# datetime,s,"
        header = "time_abs,time_rel,"
        for sensor in self.meas_data["Flow"]:
            header += f"{sensor}-flow,"
            units += "l/min,"
        for sensor in self.meas_data["Temperature"]:
            header += f"{sensor}-temperature,"
            units += "DEG C,"
        units += "\n"
        header += "\n"
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
        for port in self.ports:
            sensor_name = self.ports[port]["name"]
            sensor_type = self.ports[port]["type"]
            for property in ["flow", "temperature"]:
                sensor_name_nomad = (
                    f'{sensor_name.replace(" ", "_").replace("-", "_")}_{property}'
                )
                data.update(
                    {
                        sensor_name_nomad: {
                            # "model": "your_field_here",
                            "name": sensor_name_nomad,
                            # "sensor_id": sensor_name.split(" ")[0],
                            "attached_to": sensor_name,
                            "measured_property": property,
                            "type": sensor_type,
                            # "notes": "TE_1_K air 155 mm over crucible",
                            # "unit": self.unit[sensor_name],  # TODO
                            # "channel": channel,  # TODO
                            "value_timestamp_rel": "#/data/value_timestamp_rel",
                            "value_timestamp_abs": "#/data/value_timestamp_abs",
                        }
                    }
                )
                sensor_schema = deepcopy(sensor_schema_template)
                sensor_schema["section"]["quantities"]["value_log"]["m_annotations"][
                    "tabular"
                ]["name"] = f"{sensor_name}-{property}"
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

    def check_leakage(self):
        """Evaluate flow balance as specified in config to check for
        leakage. If leakage is detected a discord message is sent."""
        inflow = 0
        for sensor in self.inflow_sensors:
            inflow += self.last_sampling["Flow"][sensor]
        outflow = 0
        for sensor in self.outflow_sensors:
            outflow += self.last_sampling["Flow"][sensor]
        loss = inflow - outflow
        if abs(loss) > self.tolerance:
            logger.warning(
                f"Detected possible cooling water leakage, difference of {loss} l/min"
            )
            send_message(
                f"There may be a cooling water leakage.\nThe difference between measured in- and outflow is {loss} l/min."
            )


class Eurotherm:
    def __init__(self, config, name="Eurotherm"):
        """Prepare sampling.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): device name.
        """
        logger.info(f"Initializing Eurotherm device '{name}'")
        self.config = config
        self.name = name
        try:
            self.serial = Serial(**config["serial-interface"])
        except SerialException as e:
            logger.exception(f"Connection to {self.name} not possible.")
            self.serial = SerialMock()

        self.read_temperature = "\x040000PV\x05"
        self.read_op = "\x040000OP\x05"

        self.meas_data = {"Temperature": [], "Operating point": []}

    def sample(self):
        """Read sampling form device.

        Returns:
            dict: {sensor name: measurement value}
        """
        try:
            self.serial.write(self.read_temperature.encode())
            temperature = float(self.serial.readline().decode()[3:-2])
            self.serial.write(self.read_op.encode())
            op = float(self.serial.readline().decode()[3:-2])
        except Exception as e:
            logger.exception(f"Could not sample Eurotherm.")
            temperature = np.nan
            op = np.nan
        return {"Temperature": temperature, "Operating point": op}

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
        self.meas_data["Temperature"].append(sampling["Temperature"])
        self.meas_data["Operating point"].append(sampling["Operating point"])
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{sampling['Temperature']},{sampling['Operating point']},\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        units = "# datetime,s,DEG C,-,\n"
        header = "time_abs,time_rel,Temperature,Operating point,\n"
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
        for sensor_name in self.meas_data:
            sensor_name_nomad = sensor_name.replace(" ", "_").replace("-", "_")
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
                        "value_timestamp_rel": "#/data/value_timestamp_rel",
                        "value_timestamp_abs": "#/data/value_timestamp_abs",
                    }
                }
            )
            sensor_schema = deepcopy(sensor_schema_template)
            sensor_schema["section"]["quantities"]["value_log"]["m_annotations"][
                "tabular"
            ]["name"] = sensor_name
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


class OptrisIP640:
    """Optris Ip640 IR Camera."""

    def __init__(self, config, name="OptrisIP640", xml_dir="./"):
        """Initialize communication and configure device.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
            xml_dir(str, optional): Directory for xml-file with device
                configuration. Defaults to "./".
        """
        logger.info(f"Initializing OptrisIP640 device '{name}'")
        self.name = name
        self.emissivity = config["emissivity"]
        logger.info(f"{self.name} - emissivity {self.emissivity}")
        self.transmissivity = config["transmissivity"]
        logger.info(f"{self.name} - transmissivity {self.transmissivity}")
        self.t_ambient = config["T-ambient"]
        logger.info(f"{self.name} - T-ambient {self.t_ambient}")
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<imager xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<serial>{config['serial-number']}</serial>   <!-- Provide serial number, if you attach more than one camera -->
<videoformatindex>0</videoformatindex> <!-- index of the used video format (USB endpoint) -->
<formatspath>/usr/share/libirimager</formatspath>
<calipath>/usr/share/libirimager/cali</calipath>
<dppath>/root/.irimager/Cali</dppath>
<!-- Uncomment the following lines to specify user-defined parameters for the desired optic
    and temperature range. Be aware to specify meaningful parameters.
    See documentation for further information: http://evocortex.com/libirimager2/html/index.html
    By default, the first available optic and the first meaningful temperature range are selected.
-->
<fov>33</fov>
<temperature>  <!-- Messbereiche -20-100, 0-250, 150-900 -->
    <min>{config['measurement-range'][0]}</min>
    <max>{config['measurement-range'][1]}</max>
</temperature>
<optics_text></optics_text>
<framerate>{config['framerate']}</framerate>             <!-- scaled down frame rate, must be less or equal than camera frame rate -->
<bispectral>0</bispectral>              <!-- 0=only thermal sensor, 1=bispectral technology (only PI200/PI230) -->
<autoflag>
    <enable>1</enable>
    <mininterval>15.0</mininterval>
    <maxinterval>0.0</maxinterval>
</autoflag>
<tchipmode>0</tchipmode>                <!-- 0=Floating (default), 1=Auto, 2=Fixed value -->
<tchipfixedvalue>40.0</tchipfixedvalue> <!-- Fixed value for tchipmode=2 -->
<focus>50.0</focus> <!-- position of focus motor in % of range [0; 100] -->
<enable_extended_temp_range>{config['extended-T-range']}</enable_extended_temp_range> <!-- 0=Off, 1=On; Caution! Enables invalid extended temp range-->
<buffer_queue_size>5</buffer_queue_size> <!-- internal buffer queue size -->
<enable_high_precision>0</enable_high_precision> <!-- 0=Off, 1=On; Enables temperatures with more than 1 decimal places. Depends on used camera (IRImager::getTemprangeDecimal()).-->
</imager>
"""
        self.xml_file = f"{xml_dir}/{config['serial-number']}.xml"
        with open(self.xml_file, "w", encoding="utf-8") as f:
            f.write(xml)
        try:
            optris.usb_init(
                self.xml_file
            )  # This often fails on the first attempt, therefore just repeat in case of an error.
        except Exception as e:
            print(
                f"Couldn't setup OptrisIP64.\n{traceback.format_exc()}\nTrying again..."
            )
            logging.error(traceback.format_exc())
            optris.usb_init(self.xml_file)
        optris.set_radiation_parameters(
            self.emissivity, self.transmissivity, self.t_ambient
        )
        self.w, self.h = optris.get_thermal_image_size()
        self.meas_data = []
        self.image_counter = 1

    def sample(self):
        """Read image form device.

        Returns:
            numpy.array: IR image (2D temperature filed)
        """
        raw_image = optris.get_thermal_image(self.w, self.h)
        thermal_image = (raw_image - 1000.0) / 10.0  # convert to temperature
        return thermal_image

    @staticmethod
    def plot_to_file(sampling, filename):
        """Create a plot of the temperature distribution. This function
        has to be called from a subprocess because matplotlib is not
        threadsave.

        Args:
            sampling (numpy array): IR image as returned from sample()
            filename (str): filepath of plot
        """
        fig, ax = plt.subplots()
        ax.axis("off")
        line = ax.imshow(sampling, cmap="turbo", aspect="equal")
        divider = make_axes_locatable(ax)
        cax = divider.append_axes("right", size="5%", pad=0.05)
        fig.colorbar(line, cax=cax)
        fig.tight_layout()
        fig.savefig(filename)
        plt.close(fig)

    def init_output(self, directory="./"):
        """Initialize the output subdirectory and csv file..

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.directory = f"{directory}/{self.name}"
        os.makedirs(self.directory)
        with open(f"{self.directory}/_images.csv", "w", encoding="utf-8") as f:
            f.write("# datetime,s,filename,\n")
            f.write("time_abs,time_rel,img-name,\n")

    def save_measurement(self, time_abs, time_rel, sampling):
        """Write measurement data to files:
        - numpy array with temperature distribution
        - png file with 2D IR image
        - csv with metadata

        Args:
            time_abs (datetime): measurement timestamp.
            time_rel (float): relative time of measurement.
            sampling (numpy.array): sampling data, as returned from sample()
        """
        timediff = (
            datetime.datetime.now(datetime.timezone.utc).astimezone() - time_abs
        ).total_seconds()
        if timediff > 1:
            logger.warning(
                f"{self.name} save_measurement: time difference between event and saving of {timediff} seconds for samplint timestep {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')} - {time_rel}"
            )
        self.meas_data = sampling
        img_name = f"img_{self.image_counter:06}"
        np.savetxt(f"{self.directory}/{img_name}.csv", sampling, "%.2f")
        # plot in separate process because matplotlib is not threadsave
        multiprocessing.Process(
            target=self.plot_to_file,
            args=(sampling, f"{self.directory}/{img_name}.png"),
        ).start()
        # self.plot_to_file(sampling, f"{self.directory}/{img_name}.png")
        with open(f"{self.directory}/_images.csv", "a", encoding="utf-8") as f:
            f.write(
                f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{img_name},\n"
            )
        self.image_counter += 1

    def __del__(self):
        """Terminate IR camera communictation and remove xml."""
        optris.terminate()
        os.remove(self.xml_file)


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
        try:
            self.serial = Serial(**config["serial-interface"])
        except SerialException as e:
            logger.exception(f"Connection to {self.name} not possible.")
            self.serial = SerialMock()
        self.set_emissivity(config["emissivity"])
        self.set_transmissivity(config["transmissivity"])
        self.t90_dict = config["t90-dict"]
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
        cmd = f"{self.device_id}na\r"
        self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    @property
    def emissivity(self):
        """Read the current emissivity."""
        cmd = f"{self.device_id}em\r"
        self.serial.write(cmd.encode())
        return self._get_float()

    @property
    def transmissivity(self):
        """Read the current transmissivity."""
        cmd = f"{self.device_id}et\r"
        self.serial.write(cmd.encode())
        return self._get_float()

    @property
    def t90(self):
        """Reat the current t90 value."""
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


class PyrometerArrayLumasense:
    """Lumasense pyrometer, e.g. Series 600."""

    def __init__(self, config, name="PyrometerArrayLumasense"):
        """Setup serial interface, configure device.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
        """
        logger.info(f"Initializing PyrometerArrayLumasense device '{name}'")
        self.device_id = config["device-id"]
        self.name = name
        try:
            self.serial = Serial(**config["serial-interface"])
        except SerialException as e:
            logger.exception(f"Connection to {self.name} not possible.")
            self.serial = SerialMock()
        self.t90_dict = config["t90-dict"]
        self.meas_data = {}
        self.head_numbering = {}
        self.sensors = []
        self.emissivities = {}
        self.t90s = {}
        for sensor in config["sensors"]:
            self.sensors.append(sensor)
            head_number = config["sensors"][sensor]["head-number"]
            self.head_numbering.update({sensor: head_number})
            self.meas_data.update({sensor: []})
            self.emissivities.update({sensor: config["sensors"][sensor]["emissivity"]})
            self.t90s.update({sensor: config["sensors"][sensor]["t90"]})
            self.set_emissivity(head_number, config["sensors"][sensor]["emissivity"])
            self.set_emissivity(head_number, config["sensors"][sensor]["t90"])

    def _get_ok(self):
        """Check if command was accepted."""
        assert self.serial.readline().decode().strip() == "ok"

    def _get_float(self):
        """Read floatingpoint value."""
        string_val = self.serial.readline().decode().strip()
        return float(f"{string_val[:-1]}.{string_val[-1:]}")

    def get_heat_id(self, head_number):
        """Get the id of a certain head."""
        cmd = f"{self.device_id}A{head_number}sn\r"
        self.serial.write(cmd.encode())
        return self.serial.readline().decode().strip()

    def set_emissivity(self, head_number, emissivity):
        """Set emissivity for a certain head."""
        logger.info(
            f"{self.name} - setting emissivity {emissivity} for heat {head_number}"
        )
        cmd = f"{self.device_id}A{head_number}em{emissivity*100:05.1f}\r".replace(
            ".", ""
        )
        self.serial.write(cmd.encode())
        self._get_ok()

    def set_t90(self, head_number, t90):
        """Set t90 for a certain head."""
        logger.info(f"{self.name} - setting t90 {t90} for heat {head_number}")
        cmd = f"{self.device_id}A{head_number}ez{self.t90_dict[t90]}\r"
        self.serial.write(cmd.encode())
        self._get_ok()

    def read_sensor(self, head_number):
        """Read temperature of a certain head."""
        cmd = f"{self.device_id}A{head_number}ms\r"
        self.serial.write(cmd.encode())
        return self._get_float()

    def sample(self):
        """Read temperature form all heads.

        Returns:
            dict: {head name: temperature}.
        """
        sampling = {}
        for sensor in self.head_numbering:
            try:
                sampling.update({sensor: self.read_sensor(self.head_numbering[sensor])})
            except Exception as e:
                logger.exception(
                    f"Could not sample PyrometerArrayLumasense heat '{sensor}'."
                )
                sampling.update({sensor: np.nan})
        return sampling

    def init_otput(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        header = "time_abs,time_rel,"
        units = "# datetime,s,"
        for sensor in self.meas_data:
            header += f"{sensor},"
            units += "DEG C,"
        header += "\n"
        units += "\n"
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(units)
            f.write(header)

    def save_measurement(self, time_abs, time_rel, sampling):
        """Write measurement data to file.

        Args:
            time_abs (datetime): measurement timestamp.
            time_rel (float): relative time of measurement.
            sampling (dict): measurement data, as returned from sample()
        """
        timediff = (
            datetime.datetime.now(datetime.timezone.utc).astimezone() - time_abs
        ).total_seconds()
        if timediff > 1:
            logger.warning(
                f"{self.name} save_measurement: time difference between event and saving of {timediff} seconds for samplint timestep {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')} - {time_rel}"
            )
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},"
        for sensor in sampling:
            self.meas_data[sensor].append(sampling[sensor])
            line += f"{sampling[sensor]},"
        line += "\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)


class BaslerCamera:
    """Basler optical camera."""

    def __init__(self, config, name="BaslerCamera"):
        """Setup pypylon, configure device.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
        """
        logger.info(f"Initializing BaslerCamera device '{name}'")
        self.name = name
        self._timeout = config["timeout"]
        device_number = config["device-number"]
        tl_factory = pylon.TlFactory.GetInstance()
        self.device_name = tl_factory.EnumerateDevices()[
            device_number
        ].GetFriendlyName()
        self._device = pylon.InstantCamera()
        self._device.Attach(
            tl_factory.CreateDevice(tl_factory.EnumerateDevices()[device_number])
        )
        self._converter = pylon.ImageFormatConverter()
        self._converter.OutputPixelFormat = pylon.PixelType_BGR8packed
        self._converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
        self._name = tl_factory.EnumerateDevices()[device_number].GetFriendlyName()
        self._model_number = self._name.split(" ")[1]
        self._device_class = tl_factory.EnumerateDevices()[
            device_number
        ].GetDeviceClass()
        self._set_exposure_time(config["exposure-time"])
        self.set_frame_rate(config["frame-rate"])
        self._device.Open()
        self._device.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
        # self._device.StartGrabbing(pylon.GrabStrategy_UpcomingImage)
        self.meas_data = []
        self.image_counter = 1

    def _set_exposure_time(self, exposure_time):
        """Set exposure time."""
        logger.info(f"{self.name} - setting exposure time {exposure_time}")
        self._device.Open()
        if self._device_class == "BaslerGigE":
            assert (
                exposure_time <= self._device.ExposureTimeAbs.GetMax()
                and exposure_time >= self._device.ExposureTimeAbs.GetMin()
            )
            self._device.ExposureTimeAbs.SetValue(exposure_time)
        elif self._device_class == "BaslerUsb":
            assert (
                exposure_time <= self._device.ExposureTime.GetMax()
                and exposure_time >= self._device.ExposureTime.GetMin()
            )
            self._device.ExposureTime.SetValue(exposure_time)
        else:
            raise ValueError(f"Device class {self._device_class} is not supported!")
        self._device.Close()

    def sample(self):
        """Read latest image from device.

        Returns:
            numpy.array: image.
        """
        grab = self._device.RetrieveResult(self._timeout, pylon.TimeoutHandling_Return)
        if grab and grab.GrabSucceeded():
            image = self._converter.Convert(grab).GetArray()
        else:
            raise RuntimeError("Image grabbing failed.")
        grab.Release()
        return image

    def init_output(self, directory="./"):
        """Initialize the output subdirectory and csv file..

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.directory = f"{directory}/{self.name}"
        os.makedirs(self.directory)
        with open(f"{self.directory}/_images.csv", "w", encoding="utf-8") as f:
            f.write("# datetime,s,filename,\n")
            f.write("time_abs,time_rel,img-name,\n")
        with open(f"{self.directory}/device.txt", "w", encoding="utf-8") as f:
            f.write(self.device_name)

    def save_measurement(self, time_abs, time_rel, sampling):
        """Write measurement data to files:
        - jpg file with image
        - csv with metadata

        Args:
            time_abs (datetime): measurement timestamp.
            time_rel (float): relative time of measurement.
            sampling (numpy.array): image as returned from sample()
        """
        timediff = (
            datetime.datetime.now(datetime.timezone.utc).astimezone() - time_abs
        ).total_seconds()
        if timediff > 1:
            logger.warning(
                f"{self.name} save_measurement: time difference between event and saving of {timediff} seconds for samplint timestep {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')} - {time_rel}"
            )
        self.meas_data = sampling
        img_name = f"img_{self.image_counter:06}.jpg"
        Image.fromarray(sampling).convert("RGB").save(f"{self.directory}/{img_name}")
        with open(f"{self.directory}/_images.csv", "a", encoding="utf-8") as f:
            f.write(
                f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{img_name},\n"
            )
        self.image_counter += 1

    def set_frame_rate(self, frame_rate):
        """Set frame rate for continous sampling. The latest frame is
        then grabbed by the sample function."""
        self._device.Open()
        self._device.AcquisitionFrameRateEnable.SetValue(True)
        if self._device_class == "BaslerGigE":
            assert (
                frame_rate <= self._device.AcquisitionFrameRateAbs.GetMax()
                and frame_rate >= self._device.AcquisitionFrameRateAbs.GetMin()
            )
            self._device.AcquisitionFrameRateAbs.SetValue(frame_rate)
        elif self._device_class == "BaslerUsb":
            assert (
                frame_rate <= self._device.AcquisitionFrameRate.GetMax()
                and frame_rate >= self._device.AcquisitionFrameRate.GetMin()
            )
            self._device.AcquisitionFrameRate.SetValue(frame_rate)
        else:
            raise ValueError(f"Device class {self._device_class} is not supported!")
        self._device.Close()

    def __del__(self):
        """Stopp sampling, reset device."""
        self._device.StopGrabbing()
        self._device.Close()


class ProcessConditionLogger:
    """Virtual device for logging of process contidions. Instead of
    sampling a physical devices the sampling are read from the user
    input fields in the GUI."""

    def __init__(self, config, name="ProcessConditionLogger"):
        """Prepare sampling.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): device name.
        """
        self.config = config
        self.name = name
        self.meas_data = {}
        self.condition_units = {}
        for condition in config:
            default = ""
            if "default" in config[condition]:
                default = config[condition]["default"]
            self.meas_data.update({condition: default})
            if "unit" in config[condition]:
                self.condition_units.update({condition: config[condition]["unit"]})
            else:
                self.condition_units.update({condition: ""})
        self.last_meas_data = deepcopy(self.meas_data)

    def init_output(self, directory="./"):
        """Initialize the csv output file.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        self.filename = f"{directory}/{self.name}.csv"
        header = "time_abs,time_rel,"
        units = "# datetime,s,"
        for condition in self.meas_data:
            header += f"{condition},"
            units += f"{self.condition_units[condition]},"
        header += "\n"
        units += "\n"
        with open(self.filename, "w", encoding="utf-8") as f:
            f.write(units)
            f.write(header)
        self.protocol_filename = f"{directory}/protocol_{self.name}.md"
        with open(self.protocol_filename, "w", encoding="utf-8") as f:
            f.write("# Multilog protocol\n\n")
            multilog_version = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--dirty", "--always"]
                )
                .strip()
                .decode("utf-8")
            )
            f.write(f"This is multilog version {multilog_version}.\n")
            f.write(
                f"Logging stated at {datetime.datetime.now():%d.%m.%Y, %H:%M:%S}.\n\n"
            )
            f.write("## Initial process conditions\n\n")
            for condition in self.meas_data:
                f.write(
                    f"- {condition}: {self.meas_data[condition]} {self.condition_units[condition]}\n"
                )
            f.write("\n## Process condition log\n\n")

    def sample(self):
        """This function just exists to fit into the sampling structure
        of multilog. Data is directly updated upon changes in the GUI.

        Returns:
            dict: {process condition: user input}
        """
        # meas_data is updated by the widget if changes are made. No real sampling required.
        return self.meas_data

    def save_measurement(self, time_abs, time_rel, sampling):
        """Write sampling data to file. This function creates to files:
        - A csv file with all values for each timestep (follwoing the
        standard sampling procedure)
        - A readme.md file with the initial values and timestamp + value
        for each change in the process conditons (similar as people
        write it to their labbook)

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
        line = f"{time_abs.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},"
        for condition in sampling:
            line += f"{sampling[condition]},"
        line += "\n"
        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(line)

        if self.meas_data != self.last_meas_data and time_rel > 1:
            with open(self.protocol_filename, "a", encoding="utf-8") as f:
                for condition in self.meas_data:
                    if self.meas_data[condition] != self.last_meas_data[condition]:
                        f.write(
                            f"- {time_abs.strftime('%d.%m.%Y, %H:%M:%S')}, {time_rel:.1f} s, {condition}: {self.meas_data[condition]} {self.condition_units[condition]}\n"
                        )
            self.last_meas_data = deepcopy(self.meas_data)
