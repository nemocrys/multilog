import datetime
import logging
import os
import shutil


logger = logging.getLogger(__name__)
try:
    from pypylon import pylon
except Exception as e:
    logger.warning("Could not import pypylon.", exc_info=True)
try:
    from PIL import Image
except Exception as e:
    logger.warning("Could not import PIL.", exc_info=True)


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
        self.base_directory = directory
        self.directory = f"{directory}/{self.name}"
        os.makedirs(self.directory)
        with open(f"{self.directory}/_images.csv", "w", encoding="utf-8") as f:
            f.write("# datetime,s,filename,\n")
            f.write("time_abs,time_rel,img-name,\n")
        with open(f"{self.directory}/device.txt", "w", encoding="utf-8") as f:
            f.write(self.device_name)
        self.write_nomad_files(directory)

    def write_nomad_files(self, directory="./"):
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
        with open(f"{self.base_directory}/{self.name}.archive.yaml", "a") as f:  # todo
            f.write(f"  - name: {img_name}\n")
            f.write(f"    image: {self.name}/{img_name}\n")
            f.write(f"    timestamp_rel: {time_rel}\n")
            f.write(
                f"    timestamp_abs: {time_abs.isoformat(timespec='milliseconds').replace('T', ' ')}\n"
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
