from copy import deepcopy
import datetime
import logging
import subprocess
import yaml


logger = logging.getLogger(__name__)


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
            if "comment" in self.config[sensor_name]:
                data[sensor_name_nomad].update({"comment": self.config[sensor_name]["comment"]})
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
