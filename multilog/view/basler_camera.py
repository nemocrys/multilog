import logging
import time
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QFrame,
    QLineEdit,
    QSplitter,
    QLabel,
    QCheckBox,
    QGroupBox,
    QLineEdit,
)
import pyqtgraph as pg

from .base_classes import ImageWidget
from ..devices.basler_camera import BaslerCamera

logger = logging.getLogger(__name__)

class LineEdit(QLineEdit):
    """Modified of QLineEdit: red color if modified and not saved."""

    def __init__(self, parent=None):
        super(LineEdit, self).__init__(parent)

    def focusInEvent(self, e):
        super(LineEdit, self).focusInEvent(e)
        self.setStyleSheet("color: red")
        self.selectAll()

    def mousePressEvent(self, e):
        self.setStyleSheet("color: red")
        self.selectAll()

class BaslerCameraWidget(ImageWidget):
    def __init__(self, basler_camera: BaslerCamera, parent=None):
        """GUI widget of Basler optical camera.

        Args:
            basler_camera (BaslerCamera): BaslerCamera device including
                configuration information.
        """
        logger.info(f"Setting up BaslerCameraWidget  for device {basler_camera.name}")
        super().__init__(parent)
        self.cam = basler_camera

        # Camera Settings
        self.group_box_plot = QGroupBox("Camera settings")
        self.group_box_plot_layout = QGridLayout()
        self.group_box_plot.setLayout(self.group_box_plot_layout)
        self.parameter_layout.addWidget(self.group_box_plot)
        self.parameter_layout.setAlignment(self.group_box_plot, Qt.AlignTop)

        # Exposure Time
        self.lbl_exp_edit = QLabel("Exposure Time [ms]: ")
        self.lbl_exp_edit.setFont(QFont("Times", 12))
        self.lbl_exp_edit.setAlignment(Qt.AlignRight)
        self.group_box_plot_layout.addWidget(self.lbl_exp_edit, 0, 0, 1, 1)
        self.group_box_plot_layout.setAlignment(self.lbl_exp_edit, Qt.AlignBottom)

        self.edit_exp_edit = LineEdit()
        self.edit_exp_edit.setFixedWidth(90)
        self.edit_exp_edit.setFont(QFont("Times", 14, QFont.Bold))
        self.edit_exp_edit.setText(str(basler_camera.get_exposure_time()))
        self.group_box_plot_layout.addWidget(self.edit_exp_edit, 0, 1, 1, 1)
        self.group_box_plot_layout.setAlignment(self.edit_exp_edit, Qt.AlignBottom)
        self.edit_exp_edit.editingFinished.connect(self.update_edit_exp)

        # Camera Frame Rate
        self.lbl_fps_edit = QLabel("Device Framerate [ms]: ")
        self.lbl_fps_edit.setFont(QFont("Times", 12))
        self.lbl_fps_edit.setAlignment(Qt.AlignRight)
        self.group_box_plot_layout.addWidget(self.lbl_fps_edit, 1, 0, 1, 1)
        self.group_box_plot_layout.setAlignment(self.lbl_fps_edit, Qt.AlignBottom)

        self.edit_fps_edit = LineEdit()
        self.edit_fps_edit.setFixedWidth(90)
        self.edit_fps_edit.setFont(QFont("Times", 14, QFont.Bold))
        self.edit_fps_edit.setText(str(basler_camera.get_frame_rate()))
        self.group_box_plot_layout.addWidget(self.edit_fps_edit, 1, 1, 1, 1)
        self.group_box_plot_layout.setAlignment(self.edit_fps_edit, Qt.AlignBottom)
        self.edit_fps_edit.editingFinished.connect(self.update_fps)
        
        # Multilog Frame Rate
        self.lbl_fps_multi = QLabel("Saving Framerate [ms]: ")
        self.lbl_fps_multi.setFont(QFont("Times", 12))
        self.lbl_fps_multi.setAlignment(Qt.AlignRight)
        self.group_box_plot_layout.addWidget(self.lbl_fps_multi, 2, 0, 1, 1)
        self.group_box_plot_layout.setAlignment(self.lbl_fps_multi, Qt.AlignBottom)

        self.edit_fps_multi = LineEdit()
        self.edit_fps_multi.setFixedWidth(90)
        self.edit_fps_multi.setFont(QFont("Times", 14, QFont.Bold))
        self.edit_fps_multi.setText(str(basler_camera.get_frame_rate_multilog())) # EDIT 
        self.group_box_plot_layout.addWidget(self.edit_fps_multi, 2, 1, 1, 1)
        self.group_box_plot_layout.setAlignment(self.edit_fps_multi, Qt.AlignBottom)
        self.edit_fps_multi.editingFinished.connect(self.update_fps_multi)
        
        # Data Storage Checkbox
        self.lbl_emty = QLabel(" ")
        self.lbl_emty.setFont(QFont("Times", 12))
        self.group_box_plot_layout.addWidget(self.lbl_emty, 3, 0, 1, 1)

        self.lbl_data = QLabel("Write screenshots to files: ")
        self.lbl_data.setFont(QFont("Times", 12))
        self.lbl_data.setStyleSheet("color: green")
        self.lbl_data.setAlignment(Qt.AlignRight)
        self.group_box_plot_layout.addWidget(self.lbl_data, 4, 0, 1, 1)
        self.group_box_plot_layout.setAlignment(self.lbl_data, Qt.AlignBottom)

        self.cb_data = QCheckBox()
        self.cb_data.setChecked(True)
        self.cb_data.setFont(QFont("Times", 12))
        self.cb_data.setEnabled(True)
        self.group_box_plot_layout.addWidget(self.cb_data, 4, 1, 1, 1)
        self.group_box_plot_layout.setAlignment(self.cb_data, Qt.AlignBottom)
        self.cb_data.clicked.connect(self.update_cb_data)

    def update_edit_exp(self):
        try: newExp = float(self.edit_exp_edit.text().replace(",", "."))
        except: newExp = self.cam.get_exposure_time()
        self.cam._set_exposure_time(newExp)
        time.sleep(0.1)
        self.edit_exp_edit.setText(str(self.cam.get_exposure_time()))
        self.edit_exp_edit.setStyleSheet("color: black")
        self.edit_exp_edit.clearFocus()

    def update_fps(self):
        try:    newFps = float(self.edit_fps_edit.text().replace(",", "."))
        except: newFps = self.cam.get_frame_rate()
        self.cam.set_frame_rate(newFps)
        time.sleep(0.1)
        self.edit_fps_edit.setText(str(self.cam.get_frame_rate()))
        self.edit_fps_edit.setStyleSheet("color: black")
        self.edit_fps_edit.clearFocus()
    
    def update_fps_multi(self):
        try:    newFps = float(self.edit_fps_multi.text().replace(",", "."))
        except: newFps = self.cam.get_frame_rate()
        self.cam.set_frame_rate_multilog(newFps)
        time.sleep(0.1)
        self.edit_fps_multi.setText(str(self.cam.get_frame_rate_multilog()))
        self.edit_fps_multi.setStyleSheet("color: black")
        self.edit_fps_multi.clearFocus()
    
    def update_cb_data(self):
        if self.cb_data.isChecked():
            self.cam.setEnableDataStorage(True)
            self.lbl_data.setStyleSheet("color: green")
        else:
            self.cam.setEnableDataStorage(False)
            self.lbl_data.setStyleSheet("color: red")

    def set_initialization_data(self, sampling):
        """Update image with sampling data (used before recording is
        started).

        Args:
            sampling (np.array): image.
        """
        self.set_image(np.swapaxes(sampling, 0, 1))

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data. Unused.
            meas_data (np.array): image.
        """
        self.set_image(np.swapaxes(meas_data, 0, 1))
