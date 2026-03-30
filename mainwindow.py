import logging
from typing import Dict, List

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QLabel,
    QMessageBox,
    QWidget,
    QGridLayout,
    QTabWidget,
)
from pyqtgraph import PlotWidget, PlotItem

from codec import CommandId, Command
from control import ControlBox
from device import Device
from discovery import DiscoveryBox
from measurement import Measurement
from plot import PlotTabs
from selection import SelectionBox

MIN_PORT_NUMBER = 0
MAX_PORT_NUMBER = 65535

MIN_TEST_DURATION_SECONDS = 0
MAX_TEST_DURATION_SECONDS = 3600


class MainWindow(QMainWindow):

    started_test = pyqtSignal(Device, Command)
    stopped_test = pyqtSignal(Device, Command)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RocketLab Production Automation Demo")

        # --- Widget creation ---

        self.discovery_box = DiscoveryBox()
        self.selection_box = SelectionBox()
        self.plot_tabs = PlotTabs()

        # --- Widget connections ---

        self.selection_box.confirmed_device.connect(self.plot_tabs.add_test)

        # --- Widget placement ---

        layout = QGridLayout()
        layout.addWidget(self.discovery_box, 0, 0)
        layout.addWidget(self.selection_box, 1, 0)
        layout.addWidget(self.plot_tabs, 0, 1, -1, 1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)
