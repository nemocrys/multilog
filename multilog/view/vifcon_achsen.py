import logging
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QTabWidget,
)

from .base_classes import PlotWidget
from ..devices.vifcon_achsen import Vifcon_achsen

logger = logging.getLogger(__name__)


class Vifcon_achsenWidget(QWidget):
    def __init__(self, vifcon: Vifcon_achsen, parent=None):
        """GUI widget of Eurotherm controller.

        Args:
            flowmeter (Eurotherm): Eurotherm device including
                configuration information.
        """
        logger.info(f"Setting up vifcon_achsen for device {vifcon.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")

        # get Number of Axis
        
        self.hub, self.rot, self.pi = vifcon.getAxis()

        # Create NameList for every Axis
        distanceList = []
        velocityList = []
        for axis in self.hub:
            distanceList.append(f"{axis}-actual")
            distanceList.append(f"{axis}-target")
            distanceList.append(f"{axis}-upper-boundary")
            distanceList.append(f"{axis}-lower-boundary")
            velocityList.append(f"{axis}-actual")
            velocityList.append(f"{axis}-target")
            
        for axis in self.rot:
            distanceList.append(f"{axis}-angle-actual")
            velocityList.append(f"{axis}-speed-actual")
            velocityList.append(f"{axis}-speed-target")
            
        for axis in self.pi:
            distanceList.append(f"{axis}-actual")
            velocityList.append(f"{axis}-actual")

        # Create names with namelist
        self.distance_widget = PlotWidget(distanceList, "Distance", "mm")
        self.tab_widget.addTab(self.distance_widget, "Distance")
        
        self.velocity_widget = PlotWidget(velocityList, "Velocity", "mm/min")
        self.tab_widget.addTab(self.velocity_widget, "Velocity")


    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {sampling name: value}
        """

        for axis in self.hub:
            self.distance_widget.set_label(f"{axis}-actual" ,        sampling[f"{axis}"]["IWs"])
            self.distance_widget.set_label(f"{axis}-target" ,        sampling[f"{axis}"]["SWs"])
            self.distance_widget.set_label(f"{axis}-upper-boundary", sampling[f"{axis}"]["oGs"])
            self.distance_widget.set_label(f"{axis}-lower-boundary", sampling[f"{axis}"]["uGs"])
            self.velocity_widget.set_label(f"{axis}-actual" ,        sampling[f"{axis}"]["IWv"])
            self.velocity_widget.set_label(f"{axis}-target" ,        sampling[f"{axis}"]["SWv"])
        
        for axis in self.rot:
            self.distance_widget.set_label(f"{axis}-angle-actual",   sampling[f"{axis}"]["IWw"])
            self.velocity_widget.set_label(f"{axis}-speed-actual",   sampling[f"{axis}"]["IWv"])
            self.velocity_widget.set_label(f"{axis}-speed-target",   sampling[f"{axis}"]["SWv"])
            
        for axis in self.pi:
            self.distance_widget.set_label(f"{axis}-actual",          sampling[f"{axis}"]["IWs"])
            self.velocity_widget.set_label(f"{axis}-actual",          sampling[f"{axis}"]["IWv"])
            
        

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {sampling name: measurement time series}
        """
        for axis in self.hub:
            self.distance_widget.set_data(f"{axis}-actual",          rel_time, meas_data[f"{axis}"]["IWs"])
            self.distance_widget.set_data(f"{axis}-target",          rel_time, meas_data[f"{axis}"]["SWs"])
            self.distance_widget.set_data(f"{axis}-upper-boundary",  rel_time, meas_data[f"{axis}"]["oGs"])
            self.distance_widget.set_data(f"{axis}-lower-boundary",  rel_time, meas_data[f"{axis}"]["uGs"])
            self.velocity_widget.set_data(f"{axis}-actual",          rel_time, meas_data[f"{axis}"]["IWv"])
            self.velocity_widget.set_data(f"{axis}-target",          rel_time, meas_data[f"{axis}"]["SWv"])

        for axis in self.rot:
            self.distance_widget.set_data(f"{axis}-angle-actual",    rel_time, meas_data[f"{axis}"]["IWw"])
            self.velocity_widget.set_data(f"{axis}-speed-actual",    rel_time, meas_data[f"{axis}"]["IWv"])
            self.velocity_widget.set_data(f"{axis}-speed-target",    rel_time, meas_data[f"{axis}"]["SWv"])
            
        for axis in self.pi:
            self.distance_widget.set_data(f"{axis}-actual",           rel_time, meas_data[f"{axis}"]["IWs"])
            self.velocity_widget.set_data(f"{axis}-actual",           rel_time, meas_data[f"{axis}"]["IWv"])
