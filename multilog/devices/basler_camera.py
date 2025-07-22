import datetime
import logging
import os
import shutil
import numpy as np
import time

logger = logging.getLogger(__name__)
try:
    from pypylon import pylon
except Exception as e:
    logger.warning("Could not import pypylon.", exc_info=True)
try:
    from PIL import Image
except Exception as e:
    logger.warning("Could not import PIL.", exc_info=True)
try:
    from imageio import imwrite
except Exception as e:
    logger.warning("Could not import imageio.", exc_info=True)


class BaslerCamera:
    """Basler optical camera."""

    def __init__(self, config, name="BaslerCamera"):
        """Setup pypylon, configure device.

        Args:
            config (dict): device configuration (as defined in
                config.yml in the devices-section).
            name (str, optional): Device name.
        """
        self.config = config
        logger.info(f"Initializing BaslerCamera device '{name}'")
        self.name = name
        self._timeout = config["timeout"]
        device_number = config["device-number"]
        self.fileformat = config["file-format"]
        tl_factory = pylon.TlFactory.GetInstance()

        self.enableDataStorage = True
        self.debugMode         = False
        self.parameterChange   = False

        try:
            self.device_name = tl_factory.EnumerateDevices()[
                device_number
            ].GetFriendlyName()
            self._device = pylon.InstantCamera()
            self._device.Attach(
                tl_factory.CreateDevice(tl_factory.EnumerateDevices()[device_number])
            )
            self._converter = pylon.ImageFormatConverter()
            self._converter.OutputPixelFormat = pylon.PixelType_RGB8packed # change B and R if colors are wrong
            self._converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned
            self._name = tl_factory.EnumerateDevices()[device_number].GetFriendlyName()
            self._model_number = self._name.split(" ")[1]
            self._device_class = tl_factory.EnumerateDevices()[
                device_number
            ].GetDeviceClass()

            self._device.Open()

            # Set inital exposure_time and make it an externaly usable variable
            self.exposure_time = config["exposure-time"]
            self._set_exposure_time(self.exposure_time)

            # Set inital frame_rate and make it an externaly usable variable
            self.frame_rate = config["frame-rate-camera"]
            self.set_frame_rate(self.frame_rate)
            
            self._device.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)
            #self._device.StartGrabbing(pylon.GrabStrategy_UpcomingImage)
        except Exception as e:
            self.debugMode = True

            logger.error(f"Basler Camera was not mounted: {e}")
            
            self.device_name = "DEBUG-Camera"
            self._name = "DEBUG-Camera"
            self._model_number = 0

            self.exposure_time = config["exposure-time"]
            self.frame_rate    = config["frame-rate-camera"]

        self.frame_rate_multilog = config["frame-rate-multilog"]
        self.timeLastPhoto = datetime.datetime.now(datetime.timezone.utc).astimezone()
        self.meas_data = []
        self.image_counter = 1

    def sample(self):
        """Read latest image from device.

        Returns:
            numpy.array: image.
        """
        time_abs           = datetime.datetime.now(datetime.timezone.utc).astimezone()
        timeLastPhotoFloat = (time_abs - self.timeLastPhoto).total_seconds()

        if timeLastPhotoFloat >= self.frame_rate_multilog/1000:

            if self.debugMode == False:
                if self.parameterChange == False:
                    logger.debug(f"Camera {self.name} taking Photo at {self.timeLastPhoto}")
                    self.timeLastPhoto = self.round_time(datetime.datetime.now(datetime.timezone.utc).astimezone())

                    grab = self._device.RetrieveResult(self._timeout, pylon.TimeoutHandling_Return)
                    if grab.GrabSucceeded(): image = self._converter.Convert(grab).GetArray()
                    else: raise RuntimeError("Image grabbing failed.")
                    grab.Release()
                    return image

            else: #if debugmode is true
                logger.debug(f"Camera {self.name} taking Photo at {self.timeLastPhoto}")
                self.timeLastPhoto = self.round_time(datetime.datetime.now(datetime.timezone.utc).astimezone())
                m = np.ones((4000, 3000))
                n3 = np.arange(3000)
                return m*n3
        else: logger.debug(f"Camera {self.name} will take photo in {round(self.frame_rate_multilog/1000-timeLastPhotoFloat,6)} s")

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
        with open(f"{self.directory}/device.txt", "w", encoding="utf-8") as f:
            f.write(self.device_name)
        self.write_nomad_file(directory)

    def write_nomad_file(self, directory="./"):
        """Write .archive.yaml file based on device configuration.

        Args:
            directory (str, optional): Output directory. Defaults to "./".
        """
        shutil.copy(
            "./multilog/nomad/archive_template_Camera.yml",
            f"{directory}/{self.name}.archive.yaml",
        )
        with open(f"{self.base_directory}/{self.name}.archive.yaml", "a") as f:
            f.write(f"  exposure_time: {self.config['exposure-time']}\n")
            if "comment" in self.config:
                f.write(f"  comment: {self.config['comment']}\n")
            f.write(f"  images_list:\n")

    def save_measurement(self, time_abs, time_rel, sampling):
        """Write measurement data to files:
        - jpg file with image
        - csv with metadata

        Args:
            time_abs (datetime): measurement timestamp.
            time_rel (float): relative time of measurement.
            sampling (numpy.array): image as returned from sample()
        """
        timeRightNow = datetime.datetime.now(datetime.timezone.utc).astimezone() # this is bad coding, but the code has to be fast so I have to reuse this timestamp.

        timediff = (
            timeRightNow - time_abs
        ).total_seconds()
        if timediff > 1:
            logger.warning(
                f"{self.name} save_measurement: time difference between event and saving of {timediff} seconds for samplint timestep {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')} - {time_rel}"
            )
        # saving the data:
        if self.enableDataStorage == True:
            self.meas_data = sampling
            img_name = f"img_{self.image_counter:06}.{self.fileformat}"
            imwrite(f"{self.directory}/{img_name}", sampling)
            
            with open(f"{self.directory}/_images.csv", "a", encoding="utf-8") as f:
                f.write(
                    f"{timeRightNow.isoformat(timespec='milliseconds').replace('T', ' ')},{time_rel},{img_name},\n"
                )
            with open(f"{self.base_directory}/{self.name}.archive.yaml", "a") as f:  # todo
                f.write(f"  - name: {img_name}\n")
                f.write(f"    image: {self.name}/{img_name}\n")
                f.write(f"    timestamp_rel: {time_rel}\n")
                f.write(
                    f"    timestamp_abs: {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')}\n"
                )
            self.image_counter += 1
        else:
            logging.debug("No image saved. self.enableDataStorage is False")

    def _set_exposure_time(self, exposure_time):
        """Set exposure time."""
        if self.debugMode == False:
            logger.info(f"{self.name} - setting exposure time {exposure_time}")
            self.parameterChange = True
            time.sleep(0.1)
            #self._device.Open()
            if self._device_class == "BaslerGigE":
                if exposure_time <= self._device.ExposureTimeAbs.GetMax() and exposure_time >= self._device.ExposureTimeAbs.GetMin():
                    self._device.ExposureTimeAbs.SetValue(exposure_time)
                    self.exposure_time = exposure_time
            elif self._device_class == "BaslerUsb":
                if exposure_time <= self._device.ExposureTime.GetMax() and exposure_time >= self._device.ExposureTime.GetMin():
                    self._device.ExposureTime.SetValue(exposure_time)
                    self.exposure_time = exposure_time
            else:
                logger.error(f"Device class {self._device_class} is not supported!")
            #self._device.Close()
            self.parameterChange = False
        else:
            self.exposure_time = exposure_time
            logger.info(f"{self.name} - setting exposure time {exposure_time} - DEBUG MODE! No data was send to Camera")

    def get_exposure_time(self):
        return self.exposure_time

    def set_frame_rate(self, frame_rate):
        """Set frame rate for continous sampling. The latest frame is
        then grabbed by the sample function."""
        if self.debugMode == False:
            logger.info(f"{self.name} - setting frame rate {frame_rate}")
            self.parameterChange = True
            time.sleep(0.1)
            self._device.AcquisitionFrameRateEnable.SetValue(True)
            if self._device_class == "BaslerGigE":
                assert (
                    frame_rate <= self._device.AcquisitionFrameRateAbs.GetMax()
                    and frame_rate >= self._device.AcquisitionFrameRateAbs.GetMin()
                )
                self._device.AcquisitionFrameRateAbs.SetValue(frame_rate)
                self.frame_rate = frame_rate
            elif self._device_class == "BaslerUsb":
                assert (
                    frame_rate <= self._device.AcquisitionFrameRate.GetMax()
                    and frame_rate >= self._device.AcquisitionFrameRate.GetMin()
                )
                self._device.AcquisitionFrameRate.SetValue(frame_rate)
                self.frame_rate = frame_rate
            else:
                raise ValueError(f"Device class {self._device_class} is not supported!")
            self.parameterChange = False
        else:
            self.frame_rate = frame_rate
            logger.info(f"{self.name} - setting exposure time {frame_rate} - DEBUG MODE! No data was send to Camera")

    def get_frame_rate(self):
        return self.frame_rate

    def set_frame_rate_multilog(self, framerate):
        self.frame_rate_multilog = framerate

    def get_frame_rate_multilog(self):
        return self.frame_rate_multilog

    def setEnableDataStorage(self, enable):
        self.enableDataStorage = enable
    
    def getEnableDataStorage(self):
        return self.enableDataStorage

    def round_time(self, dt):
        s = dt.strftime('%Y-%m-%d %H:%M:%S.%f%z')
        head = s.split(".")[0]
        tail = "." + s.split(".")[1].split("+")[0]
        tz = s[-5:]
        f = float(tail)
        temp = "{:.01f}".format(f) 
        new_tail = temp[1:] # temp[0] is always '0'; get rid of it
        print(head + new_tail)
        return datetime.datetime.strptime(head + new_tail + tz, '%Y-%m-%d %H:%M:%S.%f%z')

    def __del__(self):
        """Stopp sampling, reset device."""
        logger.debug(f"Deleting balser camera {self}")
        if self.debugMode == False:
            self._device.StopGrabbing()
            self._device.Close()
        logger.debug(f"Stopped grabbing and closed device.")
