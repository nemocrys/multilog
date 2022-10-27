"""This module contains the main GUI window and a class for each device
implementing respective the tab.

Each device-widget must implement the following functions:
- def set_initialization_data(self, sampling: Any) -> None
- set_measurement_data(self, rel_time: list, meas_data: Any) -> None
"""


from functools import partial
import logging
from matplotlib.colors import cnames
import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QGridLayout,
    QComboBox,
    QFrame,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTabWidget,
    QScrollArea,
    QLabel,
    QCheckBox,
    QGroupBox,
)
import pyqtgraph as pg

from ..devices.daq6510 import Daq6510
from ..devices.basler_camera import BaslerCamera
from ..devices.ifm_flowmeter import IfmFlowmeter
from ..devices.eurotherm import Eurotherm
from ..devices.optris_ip640 import OptrisIP640
from ..devices.process_condition_logger import ProcessConditionLogger
from ..devices.pyrometer_array_lumasense import PyrometerArrayLumasense
from ..devices.pyrometer_lumasense import PyrometerLumasense


logger = logging.getLogger(__name__)
COLORS = [
    "red",
    "green",
    "cyan",
    "magenta",
    "blue",
    "orange",
    "darkmagenta",
    "yellow",
    "turquoise",
    "purple",
    "brown",
    "tomato",
    "lime",
    "olive",
    "navy",
    "darkmagenta",
    "beige",
    "peru",
    "grey",
    "white",
]


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


class MainWindow(QMainWindow):
    """multilog's main window."""

    def __init__(self, start_function, exit_function, parent=None):
        """Initialize main window.

        Args:
            start_function (func): function to-be-connected to start button
            exit_function (func): function to-be-connected to exit button
        """
        super().__init__(parent)
        self.start_function = start_function
        self.exit_function = exit_function

        # Main window
        self.setWindowTitle("multilog 2")
        self.setWindowIcon(QIcon("./multilog/icons/nemocrys.png"))
        self.resize(1400, 900)
        self.move(300, 10)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.central_widget.setLayout(self.main_layout)
        splitter_style_sheet = (
            "QSplitter::handle{background: LightGrey; width: 5px; height: 5px;}"
        )
        self.splitter_display = QSplitter(Qt.Vertical, frameShape=QFrame.StyledPanel)
        self.splitter_display.setChildrenCollapsible(False)
        self.splitter_display.setStyleSheet(splitter_style_sheet)
        self.main_layout.addWidget(self.splitter_display)

        # Tabs with instruments
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.tab_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFixedHeight(1000)
        self.splitter_display.addWidget(self.tab_widget)

        # Buttons and labels with main information
        self.button_widget = QWidget()
        self.button_layout = QHBoxLayout()
        self.button_widget.setLayout(self.button_layout)
        self._setup_buttons(self.button_layout)
        self.splitter_display.addWidget(self.button_widget)
        self.lbl_current_time_txt = QLabel("Current time: ")
        self.lbl_current_time_txt.setFont(QFont("Times", 12))
        self.lbl_current_time_val = QLabel("XX:XX:XX")
        self.lbl_current_time_val.setFont(QFont("Times", 12, QFont.Bold))
        self.lbl_current_time_val.setStyleSheet(f"color: blue")
        self.button_layout.addWidget(self.lbl_current_time_txt)
        self.button_layout.addWidget(self.lbl_current_time_val)
        self.lbl_start_time_txt = QLabel("Start time: ")
        self.lbl_start_time_txt.setFont(QFont("Times", 12))
        self.lbl_start_time_val = QLabel("XX.XX.XXXX XX:XX:XX")
        self.lbl_start_time_val.setFont(QFont("Times", 12, QFont.Bold))
        self.lbl_start_time_val.setStyleSheet(f"color: blue")
        self.button_layout.addWidget(self.lbl_start_time_txt)
        self.button_layout.addWidget(self.lbl_start_time_val)
        self.lbl_output_dir_txt = QLabel("Output directory: ")
        self.lbl_output_dir_txt.setFont(QFont("Times", 12))
        self.lbl_output_dir_val = QLabel("./measdata_XXXX-XX-XX_#XX")
        self.lbl_output_dir_val.setFont(QFont("Times", 12, QFont.Bold))
        self.lbl_output_dir_val.setStyleSheet(f"color: blue")
        self.button_layout.addWidget(self.lbl_output_dir_txt)
        self.button_layout.addWidget(self.lbl_output_dir_val)

    def add_tab(self, tab_widget, tab_name):
        """Add device tab to the main layout.

        Args:
            tab_widget (QWidget): widget to-be added
            tab_name (str): name of the tab
        """
        self.tab_widget.addTab(tab_widget, tab_name)

    def _setup_buttons(self, button_layout):
        self.btn_start = QPushButton()
        self.btn_start.setText("Start")
        self.btn_start.setMaximumWidth(300)
        self.btn_start.setIcon(QIcon("./multilog/icons/Start-icon.png"))
        self.btn_start.setFont(QFont("Times", 16, QFont.Bold))
        self.btn_start.setStyleSheet("color: red")
        self.btn_start.setEnabled(True)

        self.btn_exit = QPushButton()
        self.btn_exit.setText("Exit")
        self.btn_exit.setMaximumWidth(380)
        self.btn_exit.setIcon(QIcon("./multilog/icons/Exit-icon.png"))
        self.btn_exit.setFont(QFont("Times", 16, QFont.Bold))
        self.btn_exit.setStyleSheet("color: red")
        self.btn_exit.setEnabled(True)

        button_layout.addWidget(self.btn_start)
        button_layout.addWidget(self.btn_exit)
        button_layout.setSpacing(20)

        self.btn_start.clicked.connect(self.btn_start_click)
        self.btn_exit.clicked.connect(self.btn_exit_click)

    def btn_start_click(self):
        self.btn_exit.setEnabled(True)
        self.btn_start.setEnabled(False)
        self.lbl_current_time_val.setStyleSheet(f"color: red")
        self.start_function()

    def btn_exit_click(self):
        self.exit_function()

    def set_current_time(self, current_time):
        self.lbl_current_time_val.setText(f"{current_time}")

    def set_output_directory(self, output_directory):
        self.lbl_output_dir_val.setText(f"{output_directory}")

    def set_start_time(self, start_time):
        self.lbl_start_time_val.setText(f"{start_time}")


class ImageWidget(QSplitter):
    """Base class for devices displaying an image."""

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, frameShape=QFrame.StyledPanel, parent=parent)
        self.setChildrenCollapsible(True)
        self.setStyleSheet(
            "QSplitter::handle{background: LightGrey; width: 5px; height: 5px;}"
        )

        self.graphics_widget = QWidget()
        self.graphics_layout = QVBoxLayout()
        self.graphics_widget.setLayout(self.graphics_layout)
        self.addWidget(self.graphics_widget)

        self.parameter_widget = QWidget()
        self.parameter_layout = QGridLayout()
        self.parameter_widget.setLayout(self.parameter_layout)
        self.addWidget(self.parameter_widget)

        self.image_view = pg.ImageView()
        self.graphics_layout.addWidget(self.image_view)

    def set_image(self, data):
        """Set an image to be displayed.

        Args:
            data (numpy.array): image
        """
        self.image_view.setImage(data)

    def set_cmap(self, cmap_name="turbo"):
        """Set color map for the image (if data is 2D heatmap)"""
        self.cmap = pg.colormap.getFromMatplotlib(cmap_name)
        self.image_view.setColorMap(self.cmap)


class PlotWidget(QSplitter):
    """Base class for devices displaying a 2D plot."""

    def __init__(self, sensors, parameter="Temperature", unit="°C", parent=None):
        """Setup plot widget tab.

        Args:
            sensors (list): list of sensors
            parameter (str, optional): name of visualized parameter.
                Defaults to "Temperature".
            unit (str, optional): unit of visualized parameter.
                Defaults to "°C".
        """
        super().__init__(Qt.Horizontal, frameShape=QFrame.StyledPanel, parent=parent)
        self.unit = unit

        # setup main layout
        self.setChildrenCollapsible(True)
        self.setStyleSheet(
            "QSplitter::handle{background: LightGrey; width: 5px; height: 5px;}"
        )

        self.graphics_widget = QWidget()
        self.graphics_layout = QVBoxLayout()
        self.graphics_widget.setLayout(self.graphics_layout)
        self.addWidget(self.graphics_widget)

        self.parameter_widget = QWidget()
        self.parameter_layout = QGridLayout()
        self.parameter_widget.setLayout(self.parameter_layout)
        self.addWidget(self.parameter_widget)

        self.graphics_widget = pg.GraphicsLayoutWidget()
        self.graphics_layout.addWidget(self.graphics_widget)

        # setup plot
        self.plot = self.graphics_widget.addPlot()
        self.plot.showGrid(x=True, y=True)
        self.plot.setLabel("left", f"{parameter} [{unit}]")
        self.plot.setLabel("bottom", "time [s]")
        # self.plot.getAxis('top').setTicks([x2_ticks,[]])  # TODO set that!
        self.plot.enableAutoRange(axis="x")
        self.plot.enableAutoRange(axis="y")
        self.pens = []
        for color in COLORS:
            self.pens.append(pg.mkPen(color=cnames[color]))
        self.lines = {}
        for i in range(len(sensors)):
            line = self.plot.plot([], [], pen=self.pens[i])
            self.lines.update({sensors[i]: line})

        self.padding = 0.0
        self.x_min = 0
        self.x_max = 60
        self.y_min = 0
        self.y_max = 1

        # setup controls for figure scaling
        self.group_box_plot = QGroupBox("Plot confiuration")
        # self.group_box_plot.setObjectName('Group')
        # self.group_box_plot.setStyleSheet(
        #     'QGroupBox#Group{border: 1px solid black; color: black; \
        #     font-size: 16px; subcontrol-position: top left; font-weight: bold;\
        #     subcontrol-origin: margin; padding: 10px}'
        # )
        self.group_box_plot_layout = QGridLayout()
        self.group_box_plot.setLayout(self.group_box_plot_layout)
        self.parameter_layout.addWidget(self.group_box_plot)
        self.parameter_layout.setAlignment(self.group_box_plot, Qt.AlignTop)

        self.lbl_x_edit = QLabel("Time [s] : ")
        self.lbl_x_edit.setFont(QFont("Times", 12))
        self.lbl_x_edit.setAlignment(Qt.AlignRight)
        self.edit_x_min = LineEdit()
        self.edit_x_min.setFixedWidth(90)
        self.edit_x_min.setFont(QFont("Times", 14, QFont.Bold))
        self.edit_x_min.setText(str(self.x_min))
        self.edit_x_min.setEnabled(False)
        self.edit_x_max = LineEdit()
        self.edit_x_max.setFixedWidth(90)
        self.edit_x_max.setFont(QFont("Times", 14, QFont.Bold))
        self.edit_x_max.setText(str(self.x_max))
        self.edit_x_max.setEnabled(False)
        self.cb_autoscale_x = QCheckBox("Autoscale X")
        self.cb_autoscale_x.setChecked(True)
        self.cb_autoscale_x.setFont(QFont("Times", 12))
        self.cb_autoscale_x.setEnabled(True)

        self.lbl_y_edit = QLabel(f"{parameter} [{unit}] : ")
        self.lbl_y_edit.setFont(QFont("Times", 12))
        self.lbl_y_edit.setAlignment(Qt.AlignRight)
        self.edit_y_min = LineEdit()
        self.edit_y_min.setFixedWidth(90)
        self.edit_y_min.setFont(QFont("Times", 14, QFont.Bold))
        self.edit_y_min.setText(str(self.y_min))
        self.edit_y_min.setEnabled(False)
        self.edit_y_max = LineEdit()
        self.edit_y_max.setFixedWidth(90)
        self.edit_y_max.setFont(QFont("Times", 14, QFont.Bold))
        self.edit_y_max.setText(str(self.y_max))
        self.edit_y_max.setEnabled(False)
        self.cb_autoscale_y = QCheckBox("Autoscale y")
        self.cb_autoscale_y.setChecked(True)
        self.cb_autoscale_y.setFont(QFont("Times", 12))
        self.cb_autoscale_y.setEnabled(True)

        self.group_box_plot_layout.addWidget(self.lbl_x_edit, 0, 0, 1, 1)
        self.group_box_plot_layout.setAlignment(self.lbl_x_edit, Qt.AlignBottom)
        self.group_box_plot_layout.addWidget(self.edit_x_min, 0, 1, 1, 1)
        self.group_box_plot_layout.setAlignment(self.edit_x_min, Qt.AlignBottom)
        self.group_box_plot_layout.addWidget(self.edit_x_max, 0, 2, 1, 1)
        self.group_box_plot_layout.setAlignment(self.edit_x_max, Qt.AlignBottom)
        self.group_box_plot_layout.addWidget(self.cb_autoscale_x, 0, 3, 1, 3)
        self.group_box_plot_layout.setAlignment(self.cb_autoscale_x, Qt.AlignBottom)
        self.group_box_plot_layout.addWidget(self.lbl_y_edit, 1, 0, 1, 1)
        self.group_box_plot_layout.setAlignment(self.lbl_y_edit, Qt.AlignBottom)
        self.group_box_plot_layout.addWidget(self.edit_y_min, 1, 1, 1, 1)
        self.group_box_plot_layout.addWidget(self.edit_y_max, 1, 2, 1, 1)
        self.group_box_plot_layout.addWidget(self.cb_autoscale_y, 1, 3, 1, 3)

        self.cb_autoscale_x.clicked.connect(self.update_autoscale_x)
        self.cb_autoscale_y.clicked.connect(self.update_autoscale_y)
        self.edit_x_min.editingFinished.connect(self.edit_x_min_changed)
        self.edit_x_max.editingFinished.connect(self.edit_x_max_changed)
        self.edit_y_min.editingFinished.connect(self.edit_y_min_changed)
        self.edit_y_max.editingFinished.connect(self.edit_y_max_changed)

        # setup labels for sensors
        self.group_box_sensors = QGroupBox("Sensors")
        self.group_box_sensors_layout = QGridLayout()
        self.group_box_sensors.setLayout(self.group_box_sensors_layout)
        self.parameter_layout.addWidget(self.group_box_sensors)
        self.parameter_layout.setAlignment(self.group_box_sensors, Qt.AlignTop)

        self.sensor_name_labels = {}
        self.sensor_value_labels = {}
        for i in range(len(sensors)):
            lbl_name = QLabel()
            lbl_name.setText(f"{sensors[i]}:")
            lbl_name.setFont(QFont("Times", 12, QFont.Bold))
            lbl_name.setStyleSheet(f"color: {COLORS[i]}")
            self.group_box_sensors_layout.addWidget(lbl_name, i, 0, 1, 1)
            self.sensor_name_labels.update({sensors[i]: lbl_name})
            lbl_value = QLabel()
            if self.unit == "-":
                lbl_value.setText(f"XXX.XXX")
            else:
                lbl_value.setText(f"XXX.XXX {self.unit}")
            lbl_value.setFont(QFont("Times", 12, QFont.Bold))
            lbl_value.setStyleSheet(f"color: {COLORS[i]}")
            self.group_box_sensors_layout.addWidget(lbl_value, i, 1, 1, 1)
            self.sensor_value_labels.update({sensors[i]: lbl_value})

    def update_autoscale_x(self):
        if self.cb_autoscale_x.isChecked():
            self.edit_x_min.setEnabled(False)
            self.edit_x_max.setEnabled(False)
            self.plot.enableAutoRange(axis="x")
        else:
            self.edit_x_min.setEnabled(True)
            self.edit_x_max.setEnabled(True)
            self.plot.disableAutoRange(axis="x")

    def update_autoscale_y(self):
        if self.cb_autoscale_y.isChecked():
            self.edit_y_min.setEnabled(False)
            self.edit_y_max.setEnabled(False)
            self.plot.enableAutoRange(axis="y")
        else:
            self.edit_y_min.setEnabled(True)
            self.edit_y_max.setEnabled(True)
            self.plot.disableAutoRange(axis="y")

    def edit_x_min_changed(self):
        self.x_min = float(self.edit_x_min.text().replace(",", "."))
        self.edit_x_min.setText(str(self.x_min))
        self.edit_x_min.setStyleSheet("color: black")
        self.edit_x_min.clearFocus()
        self.plot.setXRange(self.x_min, self.x_max, padding=self.padding)
        self.calc_x2_ticks()

    def edit_x_max_changed(self):
        self.x_max = float(self.edit_x_max.text().replace(",", "."))
        self.edit_x_max.setText(str(self.x_max))
        self.edit_x_max.setStyleSheet("color: black")
        self.edit_x_max.clearFocus()
        self.plot.setXRange(self.x_min, self.x_max, padding=self.padding)
        self.calc_x2_ticks()

    def edit_y_min_changed(self):
        self.y_min = float(self.edit_y_min.text().replace(",", "."))
        self.edit_y_min.setText(str(self.y_min))
        self.edit_y_min.setStyleSheet("color: black")
        self.edit_y_min.clearFocus()
        self.plot.setYRange(self.y_min, self.y_max, padding=self.padding)

    def edit_y_max_changed(self):
        self.y_max = float(self.edit_y_max.text().replace(",", "."))
        self.edit_y_max.setText(str(self.y_max))
        self.edit_y_max.setStyleSheet("color: black")
        self.edit_y_max.clearFocus()
        self.plot.setYRange(self.y_min, self.y_max, padding=self.padding)

    def calc_x2_ticks(self):  # TODO
        """Not implemented. Intended to be used for a datetime axis."""
        # # calculate the datetime axis at the top x axis
        # delta_t = int(self.x_max[u] - self.x_min[u])
        # x2_min = time_start + datetime.timedelta(seconds=self.x_min[u])
        # x2_max = (x2_min + datetime.timedelta(seconds=delta_t)).strftime('%H:%M:%S')
        # x2_list = []
        # x2_ticks = []
        # for i in range(x2_Nb_ticks):
        #     x2_list.append((x2_min + datetime.timedelta(seconds=i*delta_t/(x2_Nb_ticks-1))).strftime('%H:%M:%S'))
        #     x2_ticks.append([self.x_min[u]+i*delta_t/(x2_Nb_ticks-1), x2_list[i]])
        #     self.ax_X_2[u].setTicks([x2_ticks,[]])
        pass

    def set_data(self, sensor, x, y):
        """Set data for selected sensor in plot.

        Args:
            sensor (str): name of the sensor
            x (list): x values
            y (list): y values
        """
        # PyQtGraph workaround for NaN from instrument
        x = np.array(x)
        y = np.array(y)
        con = np.isfinite(y)
        if len(y) >= 2 and y[-2:-1] != np.nan:
            y_ok = y[-2:-1]
            y[~con] = y_ok
        self.lines[sensor].setData(x, y, connect=np.logical_and(con, np.roll(con, -1)))
        if self.unit == "-":
            self.sensor_value_labels[sensor].setText(f"{y[-1]:.3f}")
        else:
            self.sensor_value_labels[sensor].setText(f"{y[-1]:.3f} {self.unit}")

    def set_label(self, sensor, val):
        """Set the label with current measurement value

        Args:
            sensor (str): name of the sensor
            val (str/float): measurement value
        """
        if self.unit == "-":
            self.sensor_value_labels[sensor].setText(f"{val:.3f}")
        else:
            self.sensor_value_labels[sensor].setText(f"{val:.3f} {self.unit}")


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


class IfmFlowmeterWidget(QWidget):
    def __init__(self, flowmeter: IfmFlowmeter, parent=None):
        """GUI widget of IFM flowmeter.

        Args:
            flowmeter (IfmFlowmeter): IfmFlowmeter device including
                configuration information.
        """
        logger.info(f"Setting up IfmFlowmeterWidget for device {flowmeter.name}")
        super().__init__(parent)
        self.layout = QGridLayout()
        self.setLayout(self.layout)
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)
        self.tab_widget.setStyleSheet("QTabBar {font-size: 14pt; color: blue;}")

        # create dicts with information required for visualization
        self.sensors = []
        for port in flowmeter.ports:
            self.sensors.append(flowmeter.ports[port]["name"])

        self.flow_widget = PlotWidget(self.sensors, "Flow", "l/min")
        self.tab_widget.addTab(self.flow_widget, "Flow")

        self.temperature_widget = PlotWidget(self.sensors, "Temperature", "°C")
        self.tab_widget.addTab(self.temperature_widget, "Temperature")

    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {
                "Flow": {sensor name: value},
                "Temperature": {sensor name: value},
            }
        """
        for sensor in self.sensors:
            self.temperature_widget.set_label(sensor, sampling["Temperature"][sensor])
            self.flow_widget.set_label(sensor, sampling["Flow"][sensor])

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {
                "Flow": {sensor name: measurement time series},
                "Temperature": {sensor name: measurement time series},
            }
        """
        for sensor in self.sensors:
            self.temperature_widget.set_data(
                sensor, rel_time, meas_data["Temperature"][sensor]
            )
            self.flow_widget.set_data(sensor, rel_time, meas_data["Flow"][sensor])


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

        self.temperature_widget = PlotWidget(["Temperature"], "Temperature", "°C")
        self.tab_widget.addTab(self.temperature_widget, "Temperature")

        self.op_widget = PlotWidget(["Operating point"], "Operating point", "-")
        self.tab_widget.addTab(self.op_widget, "Operating point")

    def set_initialization_data(self, sampling):
        """Update labels with sampling data (used before recording is
        started).

        Args:
            sampling (dict): {sampling name: value}
        """
        self.temperature_widget.set_label("Temperature", sampling["Temperature"])
        self.op_widget.set_label("Operating point", sampling["Operating point"])

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started).

        Args:
            rel_time (list): relative time of measurement data.
            meas_data (dict): {sampling name: measurement time series}
        """
        self.temperature_widget.set_data(
            "Temperature", rel_time, meas_data["Temperature"]
        )
        self.op_widget.set_data(
            "Operating point", rel_time, meas_data["Operating point"]
        )


class OptrisIP640Widget(ImageWidget):
    def __init__(self, optris_ip_640: OptrisIP640, parent=None):
        """GUI widget of Optirs Ip640 IR camera.

        Args:
            optris_ip_640 (OptrisIP640): OptrisIP640 device including
                configuration information.
        """
        logger.info(f"Setting up OptrisIP640Widget for device {optris_ip_640.name}")
        super().__init__(parent)

    def set_initialization_data(self, sampling):
        """Update image with sampling data (used before recording is
        started) using a grayscale colormap.

        Args:
            sampling (np.array): IR image.
        """
        self.set_image(sampling.T)

    def set_measurement_data(self, rel_time, meas_data):
        """Update plot and labels with measurement data (used after
        recording was started) using turbo colormap.

        Args:
            rel_time (list): relative time of measurement data. Unused.
            meas_data (np.array): IR image.
        """
        self.set_cmap("turbo")  # TODO only do that once
        self.set_image(meas_data.T)


class BaslerCameraWidget(ImageWidget):
    def __init__(self, basler_camera: BaslerCamera, parent=None):
        """GUI widget of Basler optical camera.

        Args:
            basler_camera (BaslerCamera): BaslerCamera device including
                configuration information.
        """
        logger.info(f"Setting up BaslerCameraWidget  for device {basler_camera.name}")
        super().__init__(parent)

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


class PyrometerLumasenseWidget(PlotWidget):
    def __init__(self, pyrometer: PyrometerLumasense, parent=None):
        """GUI widget of Lumasense pyrometer.

        Args:
            pyrometer (PyrometerLumasense): PyrometerLumasense device
                including configuration information.
        """
        logger.info(f"Setting up PyrometerLumasense widget for device {pyrometer.name}")
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

        self.lbl_emissivity = QLabel(f"Emissivity:\t{pyrometer.emissivity}%")
        self.lbl_emissivity.setFont(QFont("Times", 12))
        self.group_box_parameter_layout.addWidget(self.lbl_emissivity)
        self.lbl_transmissivity = QLabel(
            f"Transmissivity:\t{pyrometer.transmissivity}%"
        )
        self.lbl_transmissivity.setFont(QFont("Times", 12))
        self.group_box_parameter_layout.addWidget(self.lbl_transmissivity)
        self.lbl_t90 = QLabel(f"t90:\t\t{pyrometer.t90} s")
        self.lbl_t90.setFont(QFont("Times", 12))
        self.group_box_parameter_layout.addWidget(self.lbl_t90)

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
            lbl_emissivity = QLabel(
                f"{sensor} emissivity:\t{pyrometer_array.emissivities[sensor]*100}%"
            )
            lbl_emissivity.setFont(QFont("Times", 12))
            self.group_box_parameter_layout.addWidget(lbl_emissivity)
            lbl_t90 = QLabel(f"{sensor} t90:\t\t{pyrometer_array.t90s[sensor]} s")
            lbl_t90.setFont(QFont("Times", 12))
            self.group_box_parameter_layout.addWidget(lbl_t90)

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
