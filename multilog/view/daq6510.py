import logging
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QTabWidget,
)

from .base_classes import PlotWidget
from ..devices.daq6510 import Daq6510

logger = logging.getLogger(__name__)


class Daq6510Widget(QWidget):
    def __init__(self, daq: Daq6510, parent=None):
        """GUI widget of Kethley DAQ6510 multimeter.

        Args:
            daq (Daq6510): Daq6510 device including configuration
                information.
        """
        logger.info(f"Setting up Daq6510Widget for device {daq.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")

        # create dicts with information required for visualization
        self.tabs_sensors = {}  # tab name : sensor name
        self.sensors_tabs = {}  # sensor name : tab name
        self.tabs_units = {}  # tab name : unit name
        for channel in daq.config["channels"]:
            sensor_type = daq.config["channels"][channel]["type"].lower()
            sensor_name = daq.channel_id_names[channel]
            if sensor_type == "temperature":
                unit = "°C"
            else:
                if "unit" in daq.config["channels"][channel]:
                    unit = daq.config["channels"][channel]["unit"]
                else:
                    unit = "V"
            if "tab-name" in daq.config["channels"][channel]:
                tab_name = daq.config["channels"][channel]["tab-name"]
                if not tab_name in self.tabs_sensors:
                    self.tabs_sensors.update({tab_name: [sensor_name]})
                    self.tabs_units.update({tab_name: unit})
                else:
                    self.tabs_sensors[tab_name].append(sensor_name)
                    if unit != self.tabs_units[tab_name]:
                        raise ValueError(f"Different units given for tab {tab_name}.")
            else:
                if sensor_type == "temperature":
                    tab_name = "Temperature"
                    if not tab_name in self.tabs_sensors:
                        self.tabs_sensors.update({tab_name: [sensor_name]})
                        self.tabs_units.update({tab_name: unit})
                    else:
                        self.tabs_sensors[tab_name].append(sensor_name)
                elif sensor_type == "dcv":
                    tab_name = "DCV"
                    if not tab_name in self.tabs_sensors:
                        self.tabs_sensors.update({tab_name: [sensor_name]})
                        self.tabs_units.update({tab_name: unit})
                    else:
                        self.tabs_sensors[tab_name].append(sensor_name)
                        if unit != self.tabs_units[tab_name]:
                            raise ValueError(
                                f"Different units given for tab {tab_name}."
                            )
                elif sensor_type == "acv":
                    tab_name = "ACV"
                    if not tab_name in self.tabs_sensors:
                        self.tabs_sensors.update({tab_name: [sensor_name]})
                        self.tabs_units.update({tab_name: unit})
                    else:
                        self.tabs_sensors[tab_name].append(sensor_name)
                        if unit != self.tabs_units[tab_name]:
                            raise ValueError(
                                f"Different units given for tab {tab_name}."
                            )
            self.sensors_tabs.update({sensor_name: tab_name})

        # create widgets for each tab
        self.plot_widgets = {}
        for tab_name in self.tabs_sensors:
            plot_widget = PlotWidget(
                self.tabs_sensors[tab_name], tab_name, self.tabs_units[tab_name]
            )
            self.tab_widget.addTab(plot_widget, tab_name)
            self.plot_widgets.update({tab_name: plot_widget})

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {sensor name: measurement time series}
        """
        for sensor in meas_data:
            self.plot_widgets[self.sensors_tabs[sensor]].set_data(
                sensor, rel_time, meas_data[sensor]
            )

    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {sensor name: value}
        """
        for sensor in sampling:
            self.plot_widgets[self.sensors_tabs[sensor]].set_label(
                sensor, sampling[sensor]
            )
