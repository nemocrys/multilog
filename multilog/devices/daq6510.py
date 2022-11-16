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
        for channel in self.channel_id_names:
            sensor_name = self.channel_id_names[channel]
            sensor_name_nomad = sensor_name.replace(" ", "_").replace("-", "_")
            data.update(
                {
                    sensor_name_nomad: {
                        # "model": "your_field_here",  currently not in nomad schema
                        # "name": sensor_name_nomad,  currently not in nomad schema
                        # "sensor_id": sensor_name.split(" ")[0],  currently not in nomad schema
                        # "attached_to": " ".join(sensor_name.split(" ")[1:]),  currently not in nomad schema
                        # "measured_property": self.config["channels"][channel]["type"],  currently not in nomad schema
                        # "type": sensor_name.split("_")[0].split(" ")[0],  currently not in nomad schema
                        "value_timestamp_rel": "#/data/value_timestamp_rel",
                        "value_timestamp_abs": "#/data/value_timestamp_abs",
                    }
                }
            )
            if "comment" in self.config["channels"][channel]:
                data[sensor_name_nomad].update({"comment": self.config["channels"][channel]["comment"]})
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
