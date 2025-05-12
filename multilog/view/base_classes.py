import logging
from matplotlib.colors import cnames
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
)
import pyqtgraph as pg

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
        self.image_view.setImage(data, autoRange=False)

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
        
        try: # "regualar" methode
            x   = np.array(x)
            y   = np.array(y)
            con = np.isfinite(y)
        except: # "special" methode to catch error for X.XXE+YY notation
            x   = np.array(x)
            y   = np.array(y, dtype=float)
            con = np.isfinite(y)

        if len(y) >= 2 and y[-2:-1] != np.nan:
            y_ok = y[-2:-1]
            y[~con] = y_ok
        self.lines[sensor].setData(x, y, connect=np.logical_and(con, np.roll(con, -1)))
        if self.unit == "-":
            self.sensor_value_labels[sensor].setText(f"{y[-1]:.3f}")
        elif self.unit == "mbar": 
            self.sensor_value_labels[sensor].setText(f"{y[-1]:.3E} {self.unit}") # exeption for vifcon_gase to show the scientific format
        else:
            self.sensor_value_labels[sensor].setText(f"{y[-1]:.3f} {self.unit}")

    def set_label(self, sensor, val):
        """Set the label with current measurement value

        Args:
            sensor (str): name of the sensor
            val (str/float): measurement value
        """
        if self.unit == "-" or self.unit == "":
            self.sensor_value_labels[sensor].setText(f"{val:.3f}")
        elif self.unit == "mbar": 
            self.sensor_value_labels[sensor].setText(f"{val:.3E} {self.unit}") # exeption for vifcon_gase to show the scientific format
        else:
            self.sensor_value_labels[sensor].setText(f"{val:.3f} {self.unit}")
