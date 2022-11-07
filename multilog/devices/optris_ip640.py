import datetime
import logging
import matplotlib.pyplot as plt
import multiprocessing
import numpy as np
import os
import shutil
import traceback


logger = logging.getLogger(__name__)
try:
    from ..pyOptris import direct_binding as optris
except Exception as e:
    logger.warning(f"Could not import pyOtris", exc_info=True)
try:
    from mpl_toolkits.axes_grid1 import make_axes_locatable
except Exception as e:
    logger.warning("Could not import mpl_toolkits.", exc_info=True)


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
        self.base_directory = directory
        self.directory = f"{directory}/{self.name}"
        os.makedirs(self.directory)
        with open(f"{self.directory}/_images.csv", "w", encoding="utf-8") as f:
            f.write("# datetime,s,filename,\n")
            f.write("time_abs,time_rel,img-name,\n")
        self.write_nomad_files(directory)

    def write_nomad_files(self, directory="./"):
        """Write .archive.yaml file based on device configuration.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        shutil.copy(
            "./multilog/nomad/archive_template_IR-Camera.yml",
            f"{directory}/{self.name}.archive.yaml",
        )

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
        with open(f"{self.base_directory}/{self.name}.archive.yaml", "a") as f:  # todo
            f.write(f"  - name: {img_name}\n")
            f.write(f"    image: {img_name}.png\n")
            f.write(f"    heat_map: {img_name}.cvs\n")
            f.write(f"    timestamp_rel: {time_rel}\n")
            f.write(
                f"    timestamp_abs: {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')}\n"
            )

        self.image_counter += 1

    def __del__(self):
        """Terminate IR camera communication and remove xml."""
        optris.terminate()
        os.remove(self.xml_file)
