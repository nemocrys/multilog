import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QDoubleValidator
from PyQt5.QtWidgets import (
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QGroupBox,
    QLineEdit,
    QPushButton,
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

        row_layout = QHBoxLayout()  # Horizontales Layout für die Zeile

        # Text vor dem QLineEdit-Feld
        lbl_emissivity_label_before = QLabel(f"{self.sensor_name} emissivity:\t\t")
        lbl_emissivity_label_before.setFont(QFont("Times", 12))
        row_layout.addWidget(lbl_emissivity_label_before)

        # QLineEdit Feld
        validator = QDoubleValidator(0.0, 100.0, 1, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_edit_e = QLineEdit(self)
        self.line_edit_e.setFont(QFont("Times", 12))
        self.line_edit_e.setValidator(validator)
        self.line_edit_e.setFixedWidth(80)  # Feste Breite
        self.line_edit_e.setAlignment(Qt.AlignRight)  # Text zentrieren
        self.line_edit_e.setPlaceholderText(f"{pyrometer.emissivity*100}")
        row_layout.addWidget(self.line_edit_e)

        # Text nach dem QLineEdit-Feld
        self.label_after = QLabel("%")
        self.label_after.setFont(QFont("Times", 12))
        row_layout.addWidget(self.label_after)

        # Button zum Anpassen
        self.adjust_button = QPushButton("Change", self)
        self.pyrometer = pyrometer
        self.adjust_button.clicked.connect(self.adjust_e)
        row_layout.addWidget(self.adjust_button)

        self.group_box_parameter_layout.addLayout(row_layout) # Zeile zum Hauptlayout hinzufügen

        ### transmissivity ###
        row_layout = QHBoxLayout()

         # Text vor dem QLineEdit-Feld
        lbl_transmissivity_label_before = QLabel(f"{self.sensor_name} transmissivity:\t")
        lbl_transmissivity_label_before.setFont(QFont("Times", 12))
        row_layout.addWidget(lbl_transmissivity_label_before)

        # QLineEdit Feld
        validator = QDoubleValidator(0.0, 100.0, 1, self)
        validator.setNotation(QDoubleValidator.StandardNotation)
        self.line_edit_t = QLineEdit(self)
        self.line_edit_t.setFont(QFont("Times", 12))
        self.line_edit_t.setValidator(validator)
        self.line_edit_t.setFixedWidth(80)  # Feste Breite
        self.line_edit_t.setAlignment(Qt.AlignRight)  # Text zentrieren
        self.line_edit_t.setPlaceholderText(f"{pyrometer.transmissivity*100}")
        row_layout.addWidget(self.line_edit_t)

        # Text nach dem QLineEdit-Feld
        self.label_after = QLabel("%")
        self.label_after.setFont(QFont("Times", 12))
        row_layout.addWidget(self.label_after)

        # Button zum Anpassen
        self.adjust_button = QPushButton("Change", self)
        self.adjust_button.clicked.connect(self.adjust_t)
        row_layout.addWidget(self.adjust_button)

        self.group_box_parameter_layout.addLayout(row_layout) # Zeile zum Hauptlayout hinzufügen

    def adjust_e(self):
        new_emissivity = float(self.line_edit_e.text())/100
        if new_emissivity:
            try:
                self.pyrometer.write_e(new_emissivity)
                self.line_edit_e.setText("")
                self.line_edit_e.setPlaceholderText(str(round(self.pyrometer.read_e()*100,2)))
            except:
                 logger.exception(f"{self.sensor_name}: changing of emissivity not possible.")
                 self.line_edit_e.setText("")
    
    def adjust_t(self):
        new_transmissivity = float(self.line_edit_t.text())/100
        if new_transmissivity:
            try:
                self.pyrometer.write_t(new_transmissivity)
                self.line_edit_t.setText("")
                self.line_edit_t.setPlaceholderText(str(round(self.pyrometer.read_t(),2)))
            except:
                 logger.exception(f"{self.sensor_name}: changing of transmissivity not possible.")
                 self.line_edit_t.setText("")

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
