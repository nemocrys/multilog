from functools import partial
import logging
from matplotlib.colors import cnames
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QTabWidget,
)

from .base_classes import PlotWidget
from ..devices.ifm_flowmeter import IfmFlowmeter

logger = logging.getLogger(__name__)


class IfmFlowmeterWidget(QWidget):
    def __init__(self, flowmeter: IfmFlowmeter, parent=None):
        """GUI widget of IFM flowmeter.

        Args:
            flowmeter (IfmFlowmeter): IfmFlowmeter device including
                configuration information.
        """
        logger.info(f"Setting up IfmFlowmeterWidget for device {flowmeter.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")

        # create dicts with information required for visualization
        self.sensors = []
        for port in flowmeter.ports:
            self.sensors.append(flowmeter.ports[port]["name"])

        self.flow_widget = PlotWidget(self.sensors, "Flow", "l/min")
        self.tab_widget.addTab(self.flow_widget, "Flow")

        self.temperature_widget = PlotWidget(self.sensors, "Temperature", "°C")
        self.tab_widget.addTab(self.temperature_widget, "Temperature")

    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {
                "Flow": {sensor name: value},
                "Temperature": {sensor name: value},
            }
        """
        for sensor in self.sensors:
            self.temperature_widget.set_label(sensor, sampling["Temperature"][sensor])
            self.flow_widget.set_label(sensor, sampling["Flow"][sensor])

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {
                "Flow": {sensor name: measurement time series},
                "Temperature": {sensor name: measurement time series},
            }
        """
        for sensor in self.sensors:
            self.temperature_widget.set_data(
                sensor, rel_time, meas_data["Temperature"][sensor]
            )
            self.flow_widget.set_data(sensor, rel_time, meas_data["Flow"][sensor])
