import logging

from .base_classes import ImageWidget
from ..devices.optris_ip640 import OptrisIP640

logger = logging.getLogger(__name__)


class OptrisIP640Widget(ImageWidget):
    def __init__(self, optris_ip_640: OptrisIP640, parent=None):
        """GUI widget of Optirs Ip640 IR camera.

        Args:
            optris_ip_640 (OptrisIP640): OptrisIP640 device including
                configuration information.
        """
        logger.info(f"Setting up OptrisIP640Widget for device {optris_ip_640.name}")
        super().__init__(parent)

    def set_initialization_data(self, sampling):
        """Update image with sampling data (used before recording is
        started) using a grayscale colormap.

        Args:
            sampling (np.array): IR image.
        """
        self.set_image(sampling.T)

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started) using turbo colormap.

        Args:
            rel_time (list): relative time of measurement data. Unused.
            meas_data (np.array): IR image.
        """
        self.set_cmap("turbo")  # TODO only do that once
        self.set_image(meas_data.T)
