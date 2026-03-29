import logging
import ipaddress
from typing import Dict, List

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

from codec import CommandId, Command
from device import Device

MIN_PORT_NUMBER = 0
MAX_PORT_NUMBER = 65535

MIN_TEST_DURATION_SECONDS = 0
MAX_TEST_DURATION_SECONDS = 3600


class MainWindow(QMainWindow):

    started_test = pyqtSignal(Device, Command)
    stopped_test = pyqtSignal(Device, Command)
    requested_discovery = pyqtSignal(Device, Command)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RocketLab Production Automation Demo")
        self.available_devices: Dict[str, Device] = {}
        self.selected_device: Device | None = None

        # --- Widget creation ---

        self.device_dropdown = QComboBox()
        self.device_dropdown.setDuplicatesEnabled(False)
        self.device_placeholder = "--- select device ---"
        self.device_dropdown.addItem(self.device_placeholder)
        self.selected_device_model = QLineEdit()
        self.selected_device_serial = QLineEdit()
        self.selected_device_addr = QLineEdit()
        self.selected_device_port = QLineEdit()
        self.selected_device_model.setReadOnly(True)
        self.selected_device_serial.setReadOnly(True)
        self.selected_device_addr.setReadOnly(True)
        self.selected_device_port.setReadOnly(True)

        self.device_dropdown.activated.connect(self.show_device_info)

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

        self.xdata: List[float] = []
        self.ydata: List[float] = []
        self.window_size_seconds = 10
        self.curve = self.plot_item.plot(self.xdata, self.ydata)
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
        selection_layout.addWidget(self.device_dropdown, 0, 1, Qt.AlignmentFlag.AlignLeft)
        selection_layout.addWidget(QLabel("Model No:"), 1, 0)
        selection_layout.addWidget(QLabel("Serial No:"), 2, 0)
        selection_layout.addWidget(QLabel("IPv4 addr:"), 3, 0)
        selection_layout.addWidget(QLabel("Port No:"), 4, 0)
        selection_layout.addWidget(self.selected_device_model, 1, 1, Qt.AlignmentFlag.AlignLeft)
        selection_layout.addWidget(self.selected_device_serial, 2, 1, Qt.AlignmentFlag.AlignLeft)
        selection_layout.addWidget(self.selected_device_addr, 3, 1, Qt.AlignmentFlag.AlignLeft)
        selection_layout.addWidget(self.selected_device_port, 4, 1, Qt.AlignmentFlag.AlignLeft)
        # fmt: on

        selection_box = QGroupBox("Device selection")
        selection_box.setLayout(selection_layout)

        control_layout = QGridLayout()
        control_layout.addWidget(
            QLabel("Test duration:"), 0, 0, Qt.AlignmentFlag.AlignLeft
        )
        control_layout.addWidget(self.entry_duration, 0, 1, Qt.AlignmentFlag.AlignLeft)
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
        self.device_dropdown.clear()
        self.device_dropdown.addItem(self.device_placeholder)
        self.device_dropdown.addItems(entries)
        logging.debug(f"Added device {device}")

    @pyqtSlot(int, float, float)
    def update_plot(self, time: int, milli_volts: float, milli_amps: float) -> None:
        self.xdata.append(time / 1000)
        self.ydata.append(milli_volts)
        self.curve.setData(self.xdata, self.ydata)

        upper = self.xdata[-1]
        lower = upper - self.window_size_seconds

        if upper < self.window_size_seconds:
            upper = self.window_size_seconds
        if lower < 0:
            lower = 0

        self.plot_widget.setXRange(lower, upper)

    @pyqtSlot()
    def start_test(self) -> None:
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

        if self.selected_device is None:
            logging.debug("No device selected")
            dialog = QMessageBox(self)
            dialog.setText("Please select a device")
            dialog.exec()
            return

        logging.info("Starting test!")

        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.device_dropdown.setEnabled(False)

        command = Command(CommandId.TEST_START)
        command.params["duration"] = duration
        self.stopped_test.emit(self.selected_device, command)

    @pyqtSlot()
    def stop_test(self) -> None:
        logging.info("Stopping test!")

        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
        self.device_dropdown.setEnabled(True)

        self.stopped_test.emit(self.selected_device, Command(CommandId.TEST_STOP))

    @pyqtSlot()
    def discover_devices(self) -> None:
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
        device = Device(
            "", "", address, port
        )  # even in multicast we treat the destination as a device
        self.requested_discovery.emit(device, Command(CommandId.ID))

    @pyqtSlot()
    def show_device_info(self) -> None:
        if self.device_dropdown.currentText() == self.device_placeholder:
            self.selected_device_model.clear()
            self.selected_device_serial.clear()
            self.selected_device_addr.clear()
            self.selected_device_port.clear()
            self.selected_device = None

            return

        device = self.available_devices[self.device_dropdown.currentText()]
        self.selected_device_model.setText(device.model)
        self.selected_device_serial.setText(device.serial)
        self.selected_device_addr.setText(device.address)
        self.selected_device_port.setText(str(device.port))
        self.selected_device = device

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
