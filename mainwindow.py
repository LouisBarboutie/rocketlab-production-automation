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
        self.control_box = ControlBox()
        self.plot_tabs = PlotTabs()

        # --- Widget connections ---

        self.control_box.started_test.connect(self.start_test)
        self.control_box.stopped_test.connect(self.interrupt_test)
        self.started_test.connect(self.plot_tabs.clear_plot)
        self.stopped_test.connect(self.control_box.end_test)
        self.plot_tabs.tab_closed.connect(self.interrupt_test)
        self.selection_box.confirmed_device.connect(self.plot_tabs.add_test)

        # --- Widget placement ---

        layout = QGridLayout()
        layout.addWidget(self.discovery_box, 0, 0)
        layout.addWidget(self.selection_box, 1, 0)
        layout.addWidget(self.control_box, 2, 0)
        layout.addWidget(self.plot_tabs, 0, 1, -1, 1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    @pyqtSlot(int)
    def start_test(self, duration: int) -> None:
        if self.selection_box.selected_device is None:
            logging.debug("No device selected")
            dialog = QMessageBox(self)
            dialog.setText("Please select a device")
            dialog.exec()
            return

        logging.info("Starting test!")

        device = self.selection_box.selected_device
        if not self.plot_tabs.add_test(device):
            logging.debug(f"Test already running for {device}")
            dialog = QMessageBox(self)
            dialog.setText(
                f"Device {device.model}/{device.serial} is already being tested"
            )
            dialog.exec()
            return

        command = Command(CommandId.TEST_START)
        command.params["duration"] = duration
        self.started_test.emit(device, command)

    @pyqtSlot()
    def interrupt_test(self):
        if self.selection_box.selected_device is None:
            logging.debug("No device selected")
            dialog = QMessageBox(self)
            dialog.setText("Please select a device")
            dialog.exec()
            return

        logging.info("Interrupting test!")
        self.stopped_test.emit(
            self.selection_box.selected_device, Command(CommandId.TEST_STOP)
        )

    @pyqtSlot()
    def stop_test(self) -> None:
        logging.info("Stopping test!")
        self.control_box.end_test()
