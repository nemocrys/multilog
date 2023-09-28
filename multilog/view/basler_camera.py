import logging
import numpy as np
import pyqtgraph as pg

from .base_classes import QSplitter, ImageWidget, QGridLayout
from ..devices.basler_camera import BaslerCamera

logger = logging.getLogger(__name__)


class BaslerCameraWidget(QSplitter):
    def __init__(self, basler_camera: BaslerCamera, parent=None):
        """GUI widget of Basler optical camera.

        Args:
            basler_camera (BaslerCamera): BaslerCamera device including
                configuration information.
        """
        logger.info(f"Setting up BaslerCameraWidget  for device {basler_camera.name}")
        super().__init__(parent)
        # self.layout = QGridLayout()
        # self.setLayout(self.layout)
        self.image_widgets = []
        for i in range(len(basler_camera._devices)):
            image_widget = ImageWidget()
            self.addWidget(image_widget)
            self.image_widgets.append(image_widget)

    def set_initialization_data(self, sampling):
        """Update image with sampling data (used before recording is
        started).

        Args:
            sampling (np.array): image.
        """
        for image_widget, image in zip(self.image_widgets, sampling):
            image_widget.set_image(np.swapaxes(image, 0, 1))

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data. Unused.
            meas_data (np.array): image.
        """
        for image_widget, image in zip(self.image_widgets, meas_data):
            image_widget.set_image(np.swapaxes(image, 0, 1))
