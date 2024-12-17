import logging
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QTabWidget,
)

from .base_classes import PlotWidget
from ..devices.vifcon_generator import Vifcon_generator

logger = logging.getLogger(__name__)


class Vifcon_generatorWidget(QWidget):
    def __init__(self, vifcon: Vifcon_generator, parent=None):
        """GUI widget of Eurotherm controller.

        Args:
            flowmeter (Eurotherm): Eurotherm device including
                configuration information.
        """
        logger.info(f"Setting up vifcon_generator for device {vifcon.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")

        self.percantage_widget = PlotWidget(["power-actual", "power-target","voltage-actual", "voltage-target","current-actual", "current-target"], "Diffrent Units", "")
        self.tab_widget.addTab(self.percantage_widget, "Power, Voltage, Current")

        self.freq_widget = PlotWidget(["frequency"], "Freq", "%")
        self.tab_widget.addTab(self.freq_widget, "Freq")


    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {sampling name: value}
        """
        self.percantage_widget.set_label("power-actual", sampling["IWP"])
        self.percantage_widget.set_label("power-target", sampling["SWP"])

        self.percantage_widget.set_label("voltage-actual", sampling["IWU"])
        self.percantage_widget.set_label("voltage-target", sampling["SWU"])

        self.percantage_widget.set_label("current-actual", sampling["IWI"])
        self.percantage_widget.set_label("current-target", sampling["SWI"])

        self.freq_widget.set_label("frequency", sampling["IWf"])
        

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {sampling name: measurement time series}
        """
        
        self.percantage_widget.set_data("power-actual", rel_time, meas_data["IWP"])
        self.percantage_widget.set_data("power-target", rel_time, meas_data["SWP"])
        
        self.percantage_widget.set_data("voltage-actual", rel_time, meas_data["IWU"])
        self.percantage_widget.set_data("voltage-target", rel_time, meas_data["SWU"])
        
        self.percantage_widget.set_data("current-actual", rel_time, meas_data["IWI"])
        self.percantage_widget.set_data("current-target", rel_time, meas_data["SWI"])
        
        self.freq_widget.set_data("frequency", rel_time, meas_data["IWf"])

        

