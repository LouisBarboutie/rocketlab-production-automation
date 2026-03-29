import logging
import ipaddress
from typing import Dict

from PyQt5.QtGui import QIntValidator
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QLineEdit,
    QLabel,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QGroupBox,
    QComboBox,
)
from pyqtgraph import PlotWidget, PlotItem

from codec import CommandId
from device import Device

MIN_PORT_NUMBER = 0
MAX_PORT_NUMBER = 65535

MIN_TEST_DURATION_SECONDS = 0
MAX_TEST_DURATION_SECONDS = 3600


class MainWindow(QMainWindow):

    started_test = pyqtSignal(str, int, CommandId)
    stopped_test = pyqtSignal(str, int, CommandId)
    requested_discovery = pyqtSignal(str, int, CommandId)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RocketLab Production Automation Demo")
        self.available_devices: Dict[str, Device] = {}

        # --- Widget creation ---

        self.selected_device = QComboBox()
        self.selected_device.setDuplicatesEnabled(False)

        self.button_discover = QPushButton("Discover")
        self.button_discover.clicked.connect(self.discover_devices)

        self.entry_ip = QLineEdit()
        self.entry_ip.setText("224.3.11.15")

        self.entry_port = QLineEdit()
        self.entry_port.setValidator(QIntValidator())
        self.entry_port.setText("31115")

        self.entry_duration = QLineEdit()
        self.entry_duration.setValidator(QIntValidator())
        self.entry_duration.setText("10")

        self.button_start = QPushButton("Start")
        self.button_stop = QPushButton("Stop")
        self.button_start.clicked.connect(self.start_test)
        self.button_stop.clicked.connect(self.stop_test)

        self.plot_item = PlotItem(title="Test Plot")
        self.plot_item.setLabel("bottom", "time [s]")
        self.plot_item.setLabel("left", "Value [a.u.]")

        self.xdata = np.linspace(0, 20, 100)
        self.ydata = np.zeros_like(self.xdata)
        self.plot_item.plot(self.xdata, self.ydata)
        self.plot_widget = PlotWidget(plotItem=self.plot_item)

        # --- Widget placement ---

        # fmt:off
        discovery_layout = QGridLayout()
        discovery_layout.addWidget(QLabel("IPv4 address:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        discovery_layout.addWidget(QLabel("Port number:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        discovery_layout.addWidget(self.entry_ip, 0, 1, Qt.AlignmentFlag.AlignLeft)
        discovery_layout.addWidget(self.entry_port, 1, 1, Qt.AlignmentFlag.AlignLeft)
        discovery_layout.addWidget(self.button_discover, 3, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        # fmt: on

        discovery_box = QGroupBox("Device discovery")
        discovery_box.setLayout(discovery_layout)

        # fmt:off
        selection_layout = QGridLayout()
        selection_layout.addWidget(QLabel("Selected device:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        selection_layout.addWidget(self.selected_device, 0, 1, Qt.AlignmentFlag.AlignLeft)
        selection_layout.addWidget(QLabel("Model No:"), 1, 0)
        selection_layout.addWidget(QLabel("Serial No:"), 2, 0)
        selection_layout.addWidget(QLabel("IPv4 addr:"), 3, 0)
        selection_layout.addWidget(QLabel("Port No:"), 4, 0)
        # fmt: on

        selection_box = QGroupBox("Device selection")
        selection_box.setLayout(selection_layout)

        control_layout = QGridLayout()
        control_layout.addWidget(QLabel("Test duration:"), 0, 0)
        control_layout.addWidget(self.entry_duration, 0, 1)
        control_layout.addWidget(self.button_start, 1, 0, 1, 2)
        control_layout.addWidget(self.button_stop, 2, 0, 1, 2)

        control_box = QGroupBox("Test control")
        control_box.setLayout(control_layout)

        layout = QGridLayout()
        layout.addWidget(discovery_box, 0, 0)
        layout.addWidget(selection_box, 1, 0)
        layout.addWidget(control_box, 2, 0)
        layout.addWidget(self.plot_widget, 0, 1, -1, -1)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    @pyqtSlot(Device)
    def add_device(self, device: Device) -> None:
        self.available_devices[device.serial] = device
        entries = list(self.available_devices.keys())
        entries.sort()
        self.selected_device.clear()
        self.selected_device.addItems(entries)
        logging.debug(f"Added device {device}")

    def start_test(self):
        if not (text := self.entry_duration.text()):
            logging.debug("Missing test duration input")
            dialog = QMessageBox(self)
            dialog.setText(f"Please enter a test duration.")
            dialog.exec()
            return

        duration = int(text)
        if not MIN_TEST_DURATION_SECONDS <= duration <= MAX_TEST_DURATION_SECONDS:
            logging.debug(
                f"Duration '{duration}' is not within the range [{MIN_TEST_DURATION_SECONDS}, {MAX_TEST_DURATION_SECONDS}] seconds"
            )
            dialog = QMessageBox(self)
            dialog.setText(
                f"Please enter a test duration between {MIN_TEST_DURATION_SECONDS} and {MAX_TEST_DURATION_SECONDS} seconds"
            )
            dialog.exec()
            return

        logging.info("Starting test!")
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.xdata += 1
        self.ydata = np.sin(self.xdata)
        self.plot_item.items[0].setData(self.xdata, self.ydata)
        self.stopped_test.emit(
            self.entry_ip.text(), int(self.entry_port.text()), CommandId.TEST_START
        )

    def stop_test(self):
        logging.info("Stopping test!")
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
        self.stopped_test.emit(
            self.entry_ip.text(), int(self.entry_port.text()), CommandId.TEST_STOP
        )

    def discover_devices(self) -> None:
        self.available_devices.clear()
        """Slot for the select button"""
        address = self.entry_ip.text()
        if not address:
            logging.debug("Missing address input")
            dialog = QMessageBox(self)
            dialog.setText("Please enter a device IP address")
            dialog.exec()
            return

        if not self.is_valid_ipv4(address):
            logging.debug(f"Address '{address}' is not a valid IPv4 address!")
            dialog = QMessageBox(self)
            dialog.setText(
                f"Please enter a valid IP address. Must be in the range from 0.0.0.0 to 255.255.255.255"
            )
            dialog.exec()
            return

        if not (text := self.entry_port.text()):
            logging.debug("Missing port input")
            dialog = QMessageBox(self)
            dialog.setText(f"Please enter a device port number")
            dialog.exec()
            return

        port = int(text)
        if not MIN_PORT_NUMBER <= port <= MAX_PORT_NUMBER:
            logging.debug(
                f"Port '{port}' is not within the range [{MIN_PORT_NUMBER}, {MAX_PORT_NUMBER}]"
            )
            dialog = QMessageBox(self)
            dialog.setText(
                f"Please enter a valid port number. Must be between {MIN_PORT_NUMBER} and {MAX_PORT_NUMBER}"
            )
            dialog.exec()

            return

        logging.debug(f"Requested device discovery on {address}:{port}")
        self.requested_discovery.emit(address, port, CommandId.ID)

    @staticmethod
    def is_valid_ipv4(address: str) -> bool:
        """Checks whether the address is a valid IPv4 address.

        This check is done here and not through a QValidator, as
        the logic turns out to be quite complex. It is simpler
        to validate input on the button press rather than while
        the user gives input. QValidator side effects prevent
        changes once the first input was validated.
        """
        parts = address.split(".")
        if len(parts) != 4:
            return False
        try:
            ip = ipaddress.IPv4Address(address)
            logging.debug(f"{ip=}")
        except ValueError:
            return False

        return True
