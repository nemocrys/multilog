"""This module contains the controller-part of multilog. It sets up the
communication between device and visualization and manages the sampling
loop."""
from copy import deepcopy
import shutil
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer, QThread, QObject, pyqtSignal
import numpy as np
import datetime
import yaml
import sys
import os
import subprocess
import platform
import logging
import time


logger = logging.getLogger(__name__)


# This metaclass is required because the pyqtSignal 'signal' must be a class varaible
# see https://stackoverflow.com/questions/50294652/is-it-possible-to-create-pyqtsignals-on-instances-at-runtime-without-using-class
class SignalMetaclass(type(QObject)):
    """Metaclass used to create new signals on the fly, required to
    setup Sampler class, see
    https://stackoverflow.com/questions/50294652/is-it-possible-to-create-pyqtsignals-on-instances-at-runtime-without-using-class"""

    def __new__(cls, name, bases, dct):
        """Create new class including a pyqtSignal."""
        dct["signal"] = pyqtSignal(dict)
        return super().__new__(cls, name, bases, dct)


class Sampler(QObject, metaclass=SignalMetaclass):
    """This class is used to sample the devices from separate threads."""

    def __init__(self, devices):
        """Create sampler object

        Args:
            devices (dict): devices to be sampled.
        """
        super().__init__()
        self.devices = devices

    def update(self):
        """Sampling during initialization. Data is not saved."""
        sampling = {}
        for device in self.devices:
            try:
                logger.debug(f"Sampler: updating {device}")
                sampling.update({device: self.devices[device].sample()})
                logger.debug(f"Sampler: updated {device}")
            except Exception as e:
                logger.exception(f"Error in sampling of {device}")
        self.signal.emit(sampling)  # update graphics

    def sample(self, time):
        """Sampling during recording. Data is visualized and saved.

        Args:
            time (datetime): Global timestamp of sampling step.
        """
        time_abs = time["time_abs"]
        time_rel = time["time_rel"]
        meas_data = {}
        for device in self.devices:
            try:
                logger.debug(
                    f"Sampler: sampling {device}, timestep {time_abs.isoformat(timespec='milliseconds')} - {time_rel}"
                )
                sampling = self.devices[device].sample()
                self.devices[device].save_measurement(time_abs, time_rel, sampling)
                meas_data.update({device: self.devices[device].meas_data})
                logger.debug(f"Sampler: sampled {device}")
            except Exception as e:
                logger.exception(f"Error in sampling of {device}")
        self.signal.emit(meas_data)  # update graphics


class Controller(QObject):
    """Main class controlling multilog's sampling and data visualization."""

    # signals to communicate with threads
    signal_update_main = pyqtSignal()  # sample and update view
    signal_sample_main = pyqtSignal(dict)  # sample, update view and save
    signal_update_camera = pyqtSignal()  # sample and update view
    signal_sample_camera = pyqtSignal(dict)  # sample, update view and save

    def __init__(self, config, output_dir) -> None:
        """Initialize and run multilog.

        Args:
            config (str): File path of configuration file.
            output_dir (str): Directory where to put the output.
        """
        super().__init__()

        # load configuration, setup logging
        with open(config, encoding="utf-8") as f:
            self.config = yaml.safe_load(f)
        logging.basicConfig(**self.config["logging"])
        logging.info("initializing multilog")
        logging.info(f"configuration: {self.config}")

        self.output_dir = output_dir

        # do that after logging has been configured to log possible errors
        from .devices.daq6510 import Daq6510
        from .devices.basler_camera import BaslerCamera
        from .devices.ifm_flowmeter import IfmFlowmeter
        from .devices.eurotherm import Eurotherm
        from .devices.optris_ip640 import OptrisIP640
        from .devices.process_condition_logger import ProcessConditionLogger
        from .devices.pyrometer_array_lumasense import PyrometerArrayLumasense
        from .devices.pyrometer_lumasense import PyrometerLumasense

        from .view.main_window import MainWindow
        from .view.daq6510 import Daq6510Widget
        from .view.basler_camera import BaslerCameraWidget
        from .view.ifm_flowmeter import IfmFlowmeterWidget
        from .view.eurotherm import EurothermWidget
        from .view.optris_ip640 import OptrisIP640Widget
        from .view.process_condition_logger import ProcessConditionLoggerWidget
        from .view.pyrometer_array_lumasense import PyrometerArrayLumasenseWidget
        from .view.pyrometer_lumasense import PyrometerLumasenseWidget

        self.sampling_started = False  # this will to be true once "start" was clicked

        # setup timers that emit the signals for sampling
        # main sampling loop
        self.timer_measurement_main = QTimer()
        self.timer_measurement_main.setInterval(self.config["settings"]["dt-main"])
        self.timer_measurement_main.timeout.connect(self.sample_main)
        # camera sampling loop
        self.timer_measurement_camera = QTimer()
        self.timer_measurement_camera.setInterval(self.config["settings"]["dt-camera"])
        self.timer_measurement_camera.timeout.connect(self.sample_camera)
        # main sampling loop after startup (without saving data)
        self.timer_update_main = QTimer()
        self.timer_update_main.setInterval(self.config["settings"]["dt-init"])
        self.timer_update_main.timeout.connect(self.update_main)
        # camera frame update loop
        self.timer_update_camera = QTimer()
        self.timer_update_camera.setInterval(
            self.config["settings"]["dt-camera-update"]
        )
        self.timer_update_camera.timeout.connect(self.update_camera)

        # time information is stored globally
        # TODO this may be the reason for the race condition in IFM-flowmeter sampling
        self.start_time = None
        self.abs_time = []
        self.rel_time = []

        # setup main window
        app = QApplication(sys.argv)
        self.main_window = MainWindow(self.start, self.exit)
        if app.desktop().screenGeometry().width() == 1280:
            self.main_window.resize(1180, 900)
            self.main_window.move(10, 10)

        # setup devices & tabs
        self.devices = {}
        self.tabs = {}
        self.cameras = []
        for device_name in self.config["devices"]:
            if "DAQ-6510" in device_name:
                device = Daq6510(self.config["devices"][device_name], device_name)
                widget = Daq6510Widget(device)
            elif "IFM-flowmeter" in device_name:
                device = IfmFlowmeter(self.config["devices"][device_name], device_name)
                widget = IfmFlowmeterWidget(device)
            elif "Eurotherm" in device_name:
                device = Eurotherm(self.config["devices"][device_name], device_name)
                widget = EurothermWidget(device)
            elif "Optris-IP-640" in device_name:
                device = OptrisIP640(self.config["devices"][device_name], device_name)
                widget = OptrisIP640Widget(device)
                self.cameras.append(device_name)
            elif "IGA-6-23" in device_name or "IGAR-6-adv" in device_name:
                device = PyrometerLumasense(
                    self.config["devices"][device_name], device_name
                )
                widget = PyrometerLumasenseWidget(device)
            elif "Series-600" in device_name:
                logger.warning("Series-600 devices haven't been tested yet.")
                device = PyrometerArrayLumasense(
                    self.config["devices"][device_name], device_name
                )
                widget = PyrometerArrayLumasenseWidget(device)
            elif "Basler" in device_name:
                device = BaslerCamera(self.config["devices"][device_name], device_name)
                widget = BaslerCameraWidget(device)
                self.cameras.append(device_name)
            elif "Process-Condition-Logger" in device_name:
                device = ProcessConditionLogger(
                    self.config["devices"][device_name], device_name
                )
                widget = ProcessConditionLoggerWidget(device)
            #######################
            # add new devices here!
            #######################
            else:
                raise ValueError(f"unknown device {device_name} in config file.")

            self.devices.update({device_name: device})
            self.main_window.add_tab(widget, device_name)
            self.tabs.update({device_name: widget})

        # setup threads
        self.samplers = []
        self.threads = []
        for device in self.devices:
            thread = QThread()
            sampler = Sampler({device: self.devices[device]})
            sampler.moveToThread(thread)
            sampler.signal.connect(self.update_view)
            if device in self.cameras:
                self.signal_update_camera.connect(sampler.update)
                self.signal_sample_camera.connect(sampler.sample)
            else:
                self.signal_update_main.connect(sampler.update)
                self.signal_sample_main.connect(sampler.sample)
            self.samplers.append(sampler)
            self.threads.append(thread)

        # run
        for thread in self.threads:
            thread.start()
        self.timer_update_main.start()
        self.timer_update_camera.start()
        self.main_window.show()
        sys.exit(app.exec())

    def update_view(self, device_sampling):
        """Update the view for selected devices. This is called by the
        Sampler class's update function (using a signal).

        Args:
            device_sampling (dict): {device-name: sampling}
        """
        try:
            for device in device_sampling:
                logger.debug(f"updating view {device}")
                if not self.sampling_started:
                    self.tabs[device].set_initialization_data(device_sampling[device])
                else:
                    self.tabs[device].set_measurement_data(
                        self.rel_time, device_sampling[device]
                    )
                logger.debug(f"updated view {device}")
        except Exception as e:
            logger.exception(f"Error in updating view of {device}")

    def start(self):
        """This is executed when the start button is clicked."""
        logger.info("Stop updating.")
        self.timer_update_main.stop()
        time.sleep(1)  # to finish running update jobs (running in separate threads)
        logger.info("Start sampling.")
        self.init_output_files()
        self.start_time = datetime.datetime.now(datetime.timezone.utc).astimezone()
        self.main_window.set_start_time(self.start_time.strftime("%d.%m.%Y, %H:%M:%S"))
        self.sampling_started = True
        self.timer_measurement_main.start()
        self.sample_main()
        self.timer_measurement_camera.start()
        self.sample_camera()

    def exit(self):
        """This is executed when the exit button is clicked."""
        logger.info("Stopping sampling")
        self.timer_update_camera.stop()
        self.timer_measurement_main.stop()
        self.timer_measurement_camera.stop()
        time.sleep(1)  # to finish last sampling jobs (running in separate threads)
        for thread in self.threads:
            thread.quit()
        logger.info("Stopped sampling")
        exit()

    def init_output_files(self):
        """Create directory for sampling and initialize output files."""
        logger.info("Setting up output files.")
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        for i in range(100):
            if i == 99:
                raise ValueError("Too high directory count.")
            self.directory = f"{self.output_dir}/measdata_{date}_#{i+1:02}"
            if not os.path.exists(self.directory):
                os.makedirs(self.directory)
                break
        for device in self.devices:
            self.devices[device].init_output(self.directory)
        self.write_nomad_file()
        self.write_metadata()
        shutil.copy(
            "./multilog/nomad/base_classes.schema.archive.yaml",
            f"{self.directory}/base_classes.schema.archive.yaml",
        )
        self.main_window.set_output_directory(self.directory)

    def write_nomad_file(self):
        """Write main multilog.archive.yaml including an overview of all devices."""
        with open("./multilog/nomad/archive_template_main.yml") as f:
            nomad_dict = yaml.safe_load(f)
        data = nomad_dict.pop("data")
        multilog_version = (
            subprocess.check_output(
                ["git", "describe", "--tags", "--dirty", "--always"]
            )
            .strip()
            .decode("utf-8")
        )
        data["data_processing"].update(
            {
                "software": f"multilog {multilog_version}",
                "sampling_time": self.config["settings"]["dt-main"],
            }
        )

        inst_ir_cam = nomad_dict.pop("instrumentation_IR-camera_template")
        inst_camera = nomad_dict.pop("instrumentation_camera_template")
        inst_sensors = nomad_dict.pop("instrumentation_sensors_template")
        for device_name in self.devices:
            nomad_name = device_name.replace(" ", "_").replace("-", "_")
            if "Optris-IP-640" in device_name:
                instrument = deepcopy(inst_ir_cam)
                instrument["section"]["quantities"]["ir_camera"]["type"] = f"../upload/raw/{device_name}.archive.yaml#IR_camera"
                nomad_dict["definitions"]["sections"]["MeltCzochralski"]["sub_sections"]["instrumentation"]["section"]["sub_sections"].update(
                    {nomad_name: instrument}
                )
                data["instrumentation"][nomad_name] = {
                    "ir_camera": f"../upload/raw/{device_name}.archive.yaml#data"
                }
            elif "Basler" in device_name:
                instrument = deepcopy(inst_camera)
                instrument["section"]["quantities"]["camera"]["type"] = f"../upload/raw/{device_name}.archive.yaml#camera"
                nomad_dict["definitions"]["sections"]["MeltCzochralski"]["sub_sections"]["instrumentation"]["section"]["sub_sections"].update(
                    {nomad_name: instrument}
                )
                data["instrumentation"][nomad_name] = {
                    "camera": f"../upload/raw/{device_name}.archive.yaml#data"
                }
            else:
                instrument = deepcopy(inst_sensors)
                instrument["section"]["quantities"]["sensors_list"]["type"] = f"../upload/raw/{device_name}.archive.yaml#Sensors_list"
                nomad_dict["definitions"]["sections"]["MeltCzochralski"]["sub_sections"]["instrumentation"]["section"]["sub_sections"].update(
                    {nomad_name: instrument}
                )
                data["instrumentation"][nomad_name] = {
                    "sensors_list": f"../upload/raw/{device_name}.archive.yaml#data"
                }
        
            nomad_dict.update({"data": data})
            with open(f"{self.directory}/multilog_eln.archive.yaml", "w", encoding="utf-8") as f:
                yaml.safe_dump(nomad_dict, f, sort_keys=False)


    def write_metadata(self):
        """Write a csv file with information about multilog version,
        python version and operating system.
        """
        multilog_version = (
            subprocess.check_output(
                ["git", "describe", "--tags", "--dirty", "--always"]
            )
            .strip()
            .decode("utf-8")
        )
        metadata = f"multilog version,python version,system information,\n"
        metadata += f"{multilog_version},{platform.python_version()},{str(platform.uname()).replace(',',';')},\n"
        with open(f"{self.directory}/config.yml", "w", encoding="utf-8") as f:
            yaml.dump(self.config, f)
        with open(f"{self.directory}/metadata.csv", "w", encoding="utf-8") as f:
            f.write(metadata)

    def update_main(self):
        """Function that triggers sampling after startup (without saving).
        This function is called by a timer and leads to a call of the
        update function of the Sampler objects (running in their
        respective threads)."""
        logger.info("update main")
        self.main_window.set_current_time(datetime.datetime.now().strftime("%H:%M:%S"))
        self.signal_update_main.emit()
        if "IFM-flowmeter" in self.devices:
            flowmeter = self.devices["IFM-flowmeter"]
            flowmeter.check_leakage()

    def update_camera(self):
        """Function that triggers graphics update for cameras (without saving).
        This function is called by a timer and leads to a call of the
        update function of the Sampler objects (running in their
        respective threads)."""
        logger.info("update camera")
        self.signal_update_camera.emit()

    def sample_main(self):
        """Function that triggers sampling & saving of data.
        This function is called by a timer and leads to a call of the
        sample function of the Sampler objects (running in their
        respective threads)."""
        logger.info("sample main")
        time_abs = datetime.datetime.now(datetime.timezone.utc).astimezone()
        time_rel = round((time_abs - self.start_time).total_seconds(), 3)
        self.abs_time.append(time_abs)
        self.rel_time.append(time_rel)
        self.main_window.set_current_time(f"{time_abs:%H:%M:%S}")
        self.signal_sample_main.emit({"time_abs": time_abs, "time_rel": time_rel})
        if "IFM-flowmeter" in self.devices:
            flowmeter = self.devices["IFM-flowmeter"]
            flowmeter.check_leakage()

    def sample_camera(self):
        """Function that triggers sampling & saving of data for cameras.
        This function is called by a timer and leads to a call of the
        sample function of the Sampler objects (running in their
        respective threads)."""
        logger.info("sample camera")
        time_abs = datetime.datetime.now(datetime.timezone.utc).astimezone()
        time_rel = round((time_abs - self.start_time).total_seconds(), 3)
        self.signal_sample_camera.emit({"time_abs": time_abs, "time_rel": time_rel})


def main(config, output_dir):
    """Execute this function to run multilog.

    Args:
        config (str): File path of configuration file.
        output_dir (str): Directory where to put the output.
    """
    ctrl = Controller(config, output_dir)
