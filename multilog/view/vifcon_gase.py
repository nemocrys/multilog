import logging
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QTabWidget,
)

from .base_classes import PlotWidget
from ..devices.vifcon_gase import Vifcon_gase

logger = logging.getLogger(__name__)


class Vifcon_gaseWidget(QWidget):
    def __init__(self, vifcon: Vifcon_gase, parent=None):
        """GUI widget of Eurotherm controller.

        Args:
            flowmeter (Eurotherm): Eurotherm device including
                configuration information.
        """
        logger.info(f"Setting up vifcon_gase for device {vifcon.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")

        self.flow_widget = PlotWidget(["MFC24","MFC25","MFC26","MFC27"], "Flow", "ml/min")
        self.tab_widget.addTab(self.flow_widget, "Flow")

        self.pressure_widget = PlotWidget(["DM21","PP21","PP22"], "Pressure", "mbar")
        self.tab_widget.addTab(self.pressure_widget, "Pressure")

        self.freq_widget = PlotWidget(["PP22I"], "Freq", "%")
        self.tab_widget.addTab(self.freq_widget, "Freq")

    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {sampling name: value}
        """
        self.flow_widget.set_label("MFC24", sampling["MFC24"])
        self.flow_widget.set_label("MFC25", sampling["MFC25"])
        self.flow_widget.set_label("MFC26", sampling["MFC26"])
        self.flow_widget.set_label("MFC27", sampling["MFC27"])

        self.pressure_widget.set_label("DM21", sampling["DM21"])
        self.pressure_widget.set_label("PP21", sampling["PP21"])
        self.pressure_widget.set_label("PP22", sampling["PP22"])
        
        self.freq_widget.set_label("PP22I", sampling["PP22I"])

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {sampling name: measurement time series}
        """
        
        self.flow_widget.set_data("MFC24", rel_time, meas_data["MFC24"])
        self.flow_widget.set_data("MFC25", rel_time, meas_data["MFC25"])
        self.flow_widget.set_data("MFC26", rel_time, meas_data["MFC26"])
        self.flow_widget.set_data("MFC27", rel_time, meas_data["MFC27"])

        self.pressure_widget.set_data("DM21", rel_time, meas_data["DM21"])
        self.pressure_widget.set_data("PP21", rel_time, meas_data["PP21"])
        self.pressure_widget.set_data("PP22", rel_time, meas_data["PP22"])

        self.freq_widget.set_data("PP22I", rel_time, meas_data["PP22I"])