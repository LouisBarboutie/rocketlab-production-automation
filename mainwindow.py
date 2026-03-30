import logging
from typing import Dict, List

from PyQt5.QtGui import QIntValidator
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QLineEdit,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
    QGridLayout,
    QGroupBox,
    QComboBox,
    QTabWidget,
)
from pyqtgraph import PlotWidget, PlotItem

from codec import CommandId, Command
from control import ControlBox
from device import Device
from discovery import DiscoveryBox

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

        self.discovery_box = DiscoveryBox()
        self.control_box = ControlBox()

        self.plot_item = PlotItem(title="Test Plot")
        self.plot_item.setLabel("bottom", "time [s]")
        self.plot_item.setLabel("left", "Value [a.u.]")

        self.time: List[float] = []
        self.milli_volts: List[float] = []
        self.milli_amps: List[float] = []
        self.window_size_seconds = 10
        self.curve_volts = self.plot_item.plot()
        self.curve_amps = self.plot_item.plot()
        self.plot_widget = PlotWidget(plotItem=self.plot_item)

        self.plot_tabs = QTabWidget()
        self.plot_tabs.addTab(QWidget(), "The page")
        page = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Boo"))
        page.setLayout(layout)
        self.plot_tabs.addTab(page, "The cooler page")
        self.plot_tabs.addTab(self.plot_widget, "plot")

        # --- Widget connections ---

        self.control_box.started_test.connect(self.start_test)
        self.control_box.stopped_test.connect(self.stop_test)
        self.stopped_test.connect(self.control_box.end_test)

        # --- Widget placement ---

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

        layout = QGridLayout()
        layout.addWidget(self.discovery_box, 0, 0)
        layout.addWidget(selection_box, 1, 0)
        layout.addWidget(self.control_box, 2, 0)
        layout.addWidget(self.plot_tabs, 0, 1, -1, 1)

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
        self.time.append(time / 1000)
        self.milli_volts.append(milli_volts)
        self.milli_amps.append(milli_amps)

        self.curve_volts.setData(self.time, self.milli_volts)
        self.curve_amps.setData(self.time, self.milli_amps)

        upper = self.time[-1]
        lower = upper - self.window_size_seconds

        if upper < self.window_size_seconds:
            upper = self.window_size_seconds
        if lower < 0:
            lower = 0

        self.plot_widget.setXRange(lower, upper)

    @pyqtSlot(int)
    def start_test(self, duration: int) -> None:
        if self.selected_device is None:
            logging.debug("No device selected")
            dialog = QMessageBox(self)
            dialog.setText("Please select a device")
            dialog.exec()
            return

        logging.debug("Clearing plot")

        self.curve_volts.clear()
        self.curve_amps.clear()
        self.plot_item.update()

        self.time.clear()
        self.milli_volts.clear()
        self.milli_amps.clear()

        logging.info("Starting test!")

        self.device_dropdown.setEnabled(False)

        command = Command(CommandId.TEST_START)
        command.params["duration"] = duration
        self.started_test.emit(self.selected_device, command)

    @pyqtSlot()
    def stop_test(self) -> None:
        logging.info("Stopping test!")
        self.stopped_test.emit(self.selected_device, Command(CommandId.TEST_STOP))
        self.device_dropdown.setEnabled(True)

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
