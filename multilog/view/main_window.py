import logging
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QFrame,
    QPushButton,
    QSplitter,
    QTabWidget,
    QScrollArea,
    QLabel,
)


logger = logging.getLogger(__name__)


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
