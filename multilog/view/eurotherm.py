import logging
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QTabWidget,
)

from .base_classes import PlotWidget
from ..devices.eurotherm import Eurotherm

logger = logging.getLogger(__name__)


class EurothermWidget(QWidget):
    def __init__(self, eurotherm: Eurotherm, parent=None):
        """GUI widget of Eurotherm controller.

        Args:
            flowmeter (Eurotherm): Eurotherm device including
                configuration information.
        """
        logger.info(f"Setting up EurothermWidget for device {eurotherm.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")

        self.conectionType = eurotherm.getConectionType()

        if self.conectionType == "serial":
            self.temperature_widget = PlotWidget(["Temperature"], "Temperature", "°C")
        elif self.conectionType == "tcp":
            self.temperature_widget = PlotWidget(["Temperature-actual", "Temperature-target"], "Temperature", "°C")
        self.tab_widget.addTab(self.temperature_widget, "Temperature")

        self.op_widget = PlotWidget(["Operating point"], "Operating point", "-")
        self.tab_widget.addTab(self.op_widget, "Operating point")

    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {sampling name: value}
        """
        if self.conectionType == "serial":
            self.temperature_widget.set_label("Temperature", sampling["Temperature"])
        elif self.conectionType == "tcp":
            self.temperature_widget.set_label("Temperature-actual", sampling["IWT"])
            self.temperature_widget.set_label("Temperature-target", sampling["SWT"])
        self.op_widget.set_label("Operating point", sampling["Operating point"])

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {sampling name: measurement time series}
        """
        if self.conectionType == "serial":
            self.temperature_widget.set_data("Temperature", rel_time, meas_data["Temperature"])
        elif self.conectionType == "tcp":
            self.temperature_widget.set_data("Temperature-actual", rel_time, meas_data["IWT"])
            self.temperature_widget.set_data("Temperature-target", rel_time, meas_data["SWT"])
        self.op_widget.set_data("Operating point", rel_time, meas_data["Operating point"])
