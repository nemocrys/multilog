import datetime
import logging
import numpy as np
from serial import Serial, SerialException


logger = logging.getLogger(__name__)


class SerialMock:
    """This class is used to mock a serial interface for debugging purposes."""

    def write(self, _):
        pass

    def readline(self):
        return "".encode()


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
