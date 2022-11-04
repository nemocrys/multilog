from functools import partial
import logging
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QGridLayout,
    QComboBox,
    QLabel,
)

from .base_classes import LineEdit
from ..devices.process_condition_logger import ProcessConditionLogger


logger = logging.getLogger(__name__)


class ProcessConditionLoggerWidget(QWidget):
    def __init__(self, process_logger: ProcessConditionLogger, parent=None):
        """GUI widget for logging of process conditions.

        Args:
            process_logger (ProcessConditionLogger):
                ProcessConditionLogger device including configuration
                information.
        """
        logger.info(
            f"Setting up ProcessConditionLoggerWidget for device {process_logger.name}"
        )
        super().__init__(parent)
        self.process_logger = process_logger
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # create labels and input fields according to device configuration (read from config.yml)
        self.input_boxes = {}
        row = 0
        for condition in process_logger.config:
            if "label" in process_logger.config[condition]:
                label_name = QLabel(f"{process_logger.config[condition]['label']}:")
            else:
                label_name = QLabel(f"{condition}:")
            label_name.setFont(QFont("Times", 12))
            self.layout.addWidget(label_name, row, 0)

            default_value = ""
            if "default" in process_logger.config[condition]:
                default_value = str(
                    process_logger.config[condition]["default"]
                ).replace(",", ".")
            if "values" in process_logger.config[condition]:
                input_box = QComboBox()
                input_box.addItems(process_logger.config[condition]["values"])
                if default_value == "":
                    input_box.setCurrentIndex(-1)
                else:
                    input_box.setCurrentText(default_value)
                input_box.currentIndexChanged.connect(
                    partial(self.update_combo_condition, condition)
                )
            else:
                input_box = LineEdit()
                input_box.setText(default_value)
                input_box.returnPressed.connect(
                    partial(self.update_text_condition, condition)
                )
            input_box.setFixedWidth(320)
            input_box.setFont(QFont("Times", 12))
            self.layout.addWidget(input_box, row, 1)
            self.input_boxes.update({condition: input_box})

            label_unit = QLabel(process_logger.condition_units[condition])
            label_unit.setFont(QFont("Times", 12))
            self.layout.addWidget(label_unit, row, 2)

            row += 1

    def update_text_condition(self, condition_name):
        """This is called if the text of an input filed was changed by
        the user. The data in the ProcessConditionLogger is updated.

        Args:
            condition_name (str): name of the changed process
        """
        box = self.input_boxes[condition_name]
        box.setStyleSheet("color: black")
        box.clearFocus()
        text = box.text().replace(",", ".")
        box.setText(text)
        self.process_logger.meas_data.update({condition_name: text})

    def update_combo_condition(self, condition_name):
        """This is called if the index of an input box was changed by
        the user. The data in the ProcessConditionLogger is updated.

        Args:
            condition_name (str): name of the changed process
        """
        box = self.input_boxes[condition_name]
        box.clearFocus()
        self.process_logger.meas_data.update(
            {condition_name: box.itemText(box.currentIndex())}
        )

    def set_initialization_data(self, sampling):
        """This function exists to conform with the main sampling loop.
        It's empty because no data needs to be visualized.
        """
        pass

    def set_measurement_data(self, rel_time, meas_data):
        """This function exists to conform with the main sampling loop.
        It's empty because no data needs to be visualized.
        """
        pass
