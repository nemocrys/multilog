import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QDoubleValidator
from PyQt5.QtWidgets import (
    QGridLayout,
    QTabWidget,
    QWidget,
)

from ..devices.keysight import Keysight
from .base_classes import PlotWidget

logger = logging.getLogger(__name__)
from time import sleep

class KeysightWidget(QWidget):
    def __init__(self, oscilloscope: Keysight, parent=None):
        """GUI widget of Keysight oscilloscope.

        Args:
            oscilloscope (Keysight): Keysight device
                including configuration information.
        """
        logger.info(f"Setting up Keysight widget for device {oscilloscope.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")
        self.sensor_name = oscilloscope.name

        self.voltage_widget = PlotWidget(["VRMS AC Ch.1","VRMS DC Ch.1","VRMS AC Ch.2","VRMS DC Ch.2","VRMS AC Ch.3", "VRMS DC Ch.3","VRMS AC Ch.4", "VRMS DC Ch.4",'Wave-Generator'], "Voltage", "V")
        self.tab_widget.addTab(self.voltage_widget, "Voltage")

        self.frequency_widget = PlotWidget(["Frequency Ch.1","Frequency Ch.2","Frequency Ch.3", "Frequency Ch.4", 'Wave-Generator'], 'Frequency', 'Hz')
        self.tab_widget.addTab(self.frequency_widget, "Frequency")

    def set_initialization_data(self, sampling):
        """Update label with sampling data (used before recording is
        started).

        Args:
            sampling (float): voltage value
        """

        self.voltage_widget.set_label("VRMS AC Ch.1", sampling["VRMS AC Ch.1"])
        self.voltage_widget.set_label("VRMS AC Ch.2", sampling["VRMS AC Ch.2"])
        self.voltage_widget.set_label("VRMS AC Ch.3", sampling["VRMS AC Ch.3"])
        self.voltage_widget.set_label("VRMS AC Ch.4", sampling["VRMS AC Ch.4"])
        self.voltage_widget.set_label("VRMS DC Ch.1", sampling["VRMS DC Ch.1"])
        self.voltage_widget.set_label("VRMS DC Ch.2", sampling["VRMS DC Ch.2"])
        self.voltage_widget.set_label("VRMS DC Ch.3", sampling["VRMS DC Ch.3"])
        self.voltage_widget.set_label("VRMS DC Ch.4", sampling["VRMS DC Ch.4"])

        self.frequency_widget.set_label("Frequency Ch.1", sampling["Frequency Ch.1"])
        self.frequency_widget.set_label("Frequency Ch.2", sampling["Frequency Ch.2"])
        self.frequency_widget.set_label("Frequency Ch.3", sampling["Frequency Ch.3"])
        self.frequency_widget.set_label("Frequency Ch.4", sampling["Frequency Ch.4"])

        self.voltage_widget.set_label("Wave-Generator", sampling["WaveGen V"])   
        self.frequency_widget.set_label("Wave-Generator", sampling["WaveGen f"])

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (list): measurement time series
        """
        
        self.voltage_widget.set_data("VRMS AC Ch.1", rel_time, meas_data["VRMS AC Ch.1"])
        self.voltage_widget.set_data("VRMS AC Ch.2", rel_time, meas_data["VRMS AC Ch.2"])
        self.voltage_widget.set_data("VRMS AC Ch.3", rel_time, meas_data["VRMS AC Ch.3"])
        self.voltage_widget.set_data("VRMS AC Ch.4", rel_time, meas_data["VRMS AC Ch.4"])
        self.voltage_widget.set_data("VRMS DC Ch.1", rel_time, meas_data["VRMS DC Ch.1"])
        self.voltage_widget.set_data("VRMS DC Ch.2", rel_time, meas_data["VRMS DC Ch.2"])
        self.voltage_widget.set_data("VRMS DC Ch.3", rel_time, meas_data["VRMS DC Ch.3"])
        self.voltage_widget.set_data("VRMS DC Ch.4", rel_time, meas_data["VRMS DC Ch.4"])

        self.frequency_widget.set_data("Frequency Ch.1", rel_time, meas_data["Frequency Ch.1"])
        self.frequency_widget.set_data("Frequency Ch.2", rel_time, meas_data["Frequency Ch.2"])
        self.frequency_widget.set_data("Frequency Ch.3", rel_time, meas_data["Frequency Ch.3"])
        self.frequency_widget.set_data("Frequency Ch.4", rel_time, meas_data["Frequency Ch.4"])

        self.voltage_widget.set_data("Wave-Generator", rel_time, meas_data["WaveGen V"])   
        self.frequency_widget.set_data("Wave-Generator", rel_time, meas_data["WaveGen f"])