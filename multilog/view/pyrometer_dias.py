import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel,
    QGroupBox,
)

from ..devices.pyrometer_dias import PyrometerDias
from .base_classes import PlotWidget

logger = logging.getLogger(__name__)


class PyrometerDiasWidget(PlotWidget):
    def __init__(self, pyrometer: PyrometerDias, parent=None):
        """GUI widget of Dias pyrometer.

        Args:
            pyrometer (PyrometerDias): PyrometerLumasense device
                including configuration information.
        """
        
        logger.info(f"Setting up PyrometerDias widget for device {pyrometer.name}")
        self.sensor_name = pyrometer.name
        super().__init__(
            [self.sensor_name], parameter="Temperature", unit="°C", parent=parent
        )

        # Group box with emissivity, transmissivity, ...
        self.group_box_parameter = QGroupBox("Pyrometer configuration")
        self.group_box_parameter_layout = QVBoxLayout()
        self.group_box_parameter.setLayout(self.group_box_parameter_layout)
        self.parameter_layout.addWidget(self.group_box_parameter)
        self.parameter_layout.setAlignment(self.group_box_parameter, Qt.AlignTop)

        self.lbl_emissivity = QLabel(f"Emissivity:\t{pyrometer.emissivity}%")
        self.lbl_emissivity.setFont(QFont("Times", 12))
        self.group_box_parameter_layout.addWidget(self.lbl_emissivity)
        self.lbl_transmissivity = QLabel(
            f"Transmissivity:\t{pyrometer.transmissivity}%"
        )
        self.lbl_transmissivity.setFont(QFont("Times", 12))
        self.group_box_parameter_layout.addWidget(self.lbl_transmissivity)

    def set_initialization_data(self, sampling):
        """Update label with sampling data (used before recording is
        started).

        Args:
            sampling (float): temperature value
        """
        self.set_label(self.sensor_name, sampling)

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (list): measurement time series
        """
        self.set_data(self.sensor_name, rel_time, meas_data)
