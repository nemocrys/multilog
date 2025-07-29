import logging
import numpy as np
import pyqtgraph as pg

from .base_classes import ImageWidget
from ..devices.basler_camera import BaslerCamera

logger = logging.getLogger(__name__)


class BaslerCameraWidget(ImageWidget):
    def __init__(self, basler_camera: BaslerCamera, parent=None):
        """GUI widget of Basler optical camera.

        Args:
            basler_camera (BaslerCamera): BaslerCamera device including
                configuration information.
        """
        logger.info(f"Setting up BaslerCameraWidget  for device {basler_camera.name}")
        super().__init__(parent)

    def set_initialization_data(self, sampling):
        """Update image with sampling data (used before recording is
        started).

        Args:
            sampling (np.array): image.
        """
        self.set_image(np.swapaxes(sampling, 0, 1))

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data. Unused.
            meas_data (np.array): image.
        """
        self.set_image(np.swapaxes(meas_data, 0, 1))
