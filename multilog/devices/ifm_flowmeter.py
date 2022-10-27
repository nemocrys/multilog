import asyncio
from copy import deepcopy
import datetime
import logging
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
from os.path import expanduser
from serial import Serial, SerialException
import subprocess
import traceback
import yaml

logger = logging.getLogger(__name__)

# required for camera
try:
    import requests
except Exception as e:
    logger.warning("Could not import requests.", exc_info=True)
# required for discord bot
try:
    from dotenv import load_dotenv
except Exception as e:
    logger.warning("Could not import dotenv.", exc_info=True)
try:
    from discord.ext import commands
except Exception as e:
    logger.warning("Could not import discord.", exc_info=True)


def send_discord_message(msg):
    """Bot for sending discord messages on a pre-configured computer.
    Refer to the discord docs for additional information."""
    logger.info(f"Sending discord message '{msg}'")
    asyncio.set_event_loop(asyncio.new_event_loop())
    load_dotenv(expanduser("~") + "/discord.env")
    DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
    DISCORD_CHANNEL = int(os.getenv("DISCORD_CHANNEL"))

    bot = commands.Bot(command_prefix="cmd!", description="I am NemoOneBot")

    @bot.event
    async def on_ready():
        channel = bot.get_channel(DISCORD_CHANNEL)
        await channel.send(msg)
        await asyncio.sleep(0.5)
        await bot.close()

    bot.run(DISCORD_TOKEN)  # blocking call!


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
            send_discord_message(
                f"There may be a cooling water leakage.\nThe difference between measured in- and outflow is {loss} l/min."
            )
