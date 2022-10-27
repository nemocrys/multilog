import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QGroupBox,
)

from .base_classes import PlotWidget
from ..devices.pyrometer_array_lumasense import PyrometerArrayLumasense

logger = logging.getLogger(__name__)


class PyrometerArrayLumasenseWidget(PlotWidget):
    def __init__(self, pyrometer_array: PyrometerArrayLumasense, parent=None):
        """GUI widget of Lumasense pyrometer array.

        Args:
            pyrometer_array (PyrometerArrayLumasense):
                PyrometerArrayLumasense device including configuration
                information.
        """
        logger.info(
            f"Setting up PyrometerArrayLumasense widget for device {pyrometer_array.name}"
        )
        super().__init__(
            pyrometer_array.sensors, parameter="Temperature", unit="°C", parent=parent
        )

        # Group box with emissivity, transmissivity, ...
        self.group_box_parameter = QGroupBox("Pyrometer configuration")
        self.group_box_parameter_layout = QVBoxLayout()
        self.group_box_parameter.setLayout(self.group_box_parameter_layout)
        self.parameter_layout.addWidget(self.group_box_parameter)
        self.parameter_layout.setAlignment(self.group_box_parameter, Qt.AlignTop)

        for sensor in pyrometer_array.sensors:
            lbl_emissivity = QLabel(
                f"{sensor} emissivity:\t{pyrometer_array.emissivities[sensor]*100}%"
            )
            lbl_emissivity.setFont(QFont("Times", 12))
            self.group_box_parameter_layout.addWidget(lbl_emissivity)
            lbl_t90 = QLabel(f"{sensor} t90:\t\t{pyrometer_array.t90s[sensor]} s")
            lbl_t90.setFont(QFont("Times", 12))
            self.group_box_parameter_layout.addWidget(lbl_t90)

    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {head name: temperature}
        """
        for sensor in sampling:
            self.set_label(sensor, sampling[sensor])

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {heat name: measurement time series}
        """
        for sensor in meas_data:
            self.set_data(sensor, rel_time, meas_data)
