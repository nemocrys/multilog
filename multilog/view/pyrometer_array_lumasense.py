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
            row_layout = QHBoxLayout()  # Horizontales Layout für die Zeile

            # Text vor dem QLineEdit-Feld
            lbl_emissivity_label_before = QLabel(f"{sensor} emissivity:\t")
            lbl_emissivity_label_before.setFont(QFont("Times", 12))
            row_layout.addWidget(lbl_emissivity_label_before)

            # QLineEdit Feld
            validator = QDoubleValidator(0.0, 100.0, 1, self)
            validator.setNotation(QDoubleValidator.StandardNotation)
            line_edit_e = QLineEdit(self)
            line_edit_e.setFont(QFont("Times", 12))
            line_edit_e.setValidator(validator)
            line_edit_e.setFixedWidth(80)  # Feste Breite
            line_edit_e.setAlignment(Qt.AlignRight)  # Text zentrieren
            line_edit_e.setPlaceholderText(f"{pyrometer_array.emissivities[sensor]*100}")
            row_layout.addWidget(line_edit_e)

            # Text nach dem QLineEdit-Feld
            self.label_after = QLabel("%")
            self.label_after.setFont(QFont("Times", 12))
            row_layout.addWidget(self.label_after)

            # Button zum Anpassen
            self.adjust_button = QPushButton("Change", self)
            self.pyrometer_array = pyrometer_array
            #self.s = sensor
            self.adjust_button.clicked.connect(lambda _, e=line_edit_e, s=sensor: self.adjust_e(e, s))
            row_layout.addWidget(self.adjust_button)

            self.group_box_parameter_layout.addLayout(row_layout) # Zeile zum Hauptlayout hinzufügen

            lbl_t90 = QLabel(f"{sensor} t90:\t\t{pyrometer_array.t90s[sensor]} s")
            lbl_t90.setFont(QFont("Times", 12))
            self.group_box_parameter_layout.addWidget(lbl_t90)


    def adjust_e(self, line_edit_e, sensor):
        if line_edit_e.text() != "":
            new_emissivity = float(line_edit_e.text())
        else:
            new_emissivity = False
        if new_emissivity:
            try:
                set_emissivity(sensor, new_emissivity)
                line_edit_e.setText("")
                line_edit_e.setPlaceholderText(new_emissivity)
            except:
                 logger.exception(f"{sensor}: changing of emissivity not possible.")
                 line_edit_e.setText("")

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
