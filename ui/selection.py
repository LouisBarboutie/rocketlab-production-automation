import logging
from typing import Dict

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import (
    QGroupBox,
    QComboBox,
    QLineEdit,
    QLabel,
    QGridLayout,
    QPushButton,
)

from network.device import Device


class SelectionBox(QGroupBox):

    confirmed_device = pyqtSignal(Device)

    device_placeholder = "--- select device ---"
    available_devices: Dict[str, Device] = {}

    # allow only one global selected device for now
    selected_device: Device | None = None

    def __init__(self) -> None:
        super().__init__("Device selection")

        self.device_dropdown = QComboBox()
        self.device_dropdown.setDuplicatesEnabled(False)
        self.device_dropdown.addItem(self.device_placeholder)
        self.info_model = QLineEdit()
        self.info_serial = QLineEdit()
        self.info_addr = QLineEdit()
        self.info_port = QLineEdit()
        self.info_model.setReadOnly(True)
        self.info_serial.setReadOnly(True)
        self.info_addr.setReadOnly(True)
        self.info_port.setReadOnly(True)
        self.add_test_button = QPushButton("Add test")

        self.device_dropdown.activated.connect(self.show_device_info)
        self.add_test_button.clicked.connect(self.confirm_device)

        layout = QGridLayout()
        layout.addWidget(QLabel("Selected device:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.device_dropdown, 0, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(QLabel("Model No:"), 1, 0)
        layout.addWidget(QLabel("Serial No:"), 2, 0)
        layout.addWidget(QLabel("IPv4 addr:"), 3, 0)
        layout.addWidget(QLabel("Port No:"), 4, 0)
        layout.addWidget(self.info_model, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.info_serial, 2, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.info_addr, 3, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.info_port, 4, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.add_test_button, 5, 0, 1, 2)

        self.setLayout(layout)

    @pyqtSlot(Device)
    def add_device(self, device: Device) -> None:
        self.available_devices[device.serial] = device
        entries = list(self.available_devices.keys())
        entries.sort()
        self.device_dropdown.clear()
        self.device_dropdown.addItem(self.device_placeholder)
        self.device_dropdown.addItems(entries)
        logging.debug(f"Added device {device}")

    @pyqtSlot()
    def show_device_info(self) -> None:
        if self.device_dropdown.currentText() == self.device_placeholder:
            self.info_model.clear()
            self.info_serial.clear()
            self.info_addr.clear()
            self.info_port.clear()
            self.selected_device = None

            return

        device = self.available_devices[self.device_dropdown.currentText()]
        self.info_model.setText(device.model)
        self.info_serial.setText(device.serial)
        self.info_addr.setText(device.address.toString())
        self.info_port.setText(str(device.port))
        self.selected_device = device

    @pyqtSlot()
    def confirm_device(self) -> None:
        if self.device_dropdown.currentText() == self.device_placeholder:
            return
        self.confirmed_device.emit(self.selected_device)
