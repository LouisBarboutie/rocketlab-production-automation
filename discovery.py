import ipaddress
import logging

from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIntValidator
from PyQt5.QtNetwork import QHostAddress
from PyQt5.QtWidgets import (
    QGroupBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QGridLayout,
    QMessageBox,
)

from codec import Command, CommandId
from device import Device

# Port number is a uint16
MIN_PORT_NUMBER = 0
MAX_PORT_NUMBER = 65535


class DiscoveryBox(QGroupBox):

    requested_discovery = pyqtSignal(Device, Command)

    # default multicast address and port as per the device documentation
    default_ip = "224.3.11.15"
    default_port = "31115"

    def __init__(self):
        super().__init__("Device discovery")

        self.entry_ip = QLineEdit()
        self.entry_ip.setText(DiscoveryBox.default_ip)

        self.entry_port = QLineEdit()
        self.entry_port.setValidator(QIntValidator())
        self.entry_port.setText(DiscoveryBox.default_port)

        self.button_discover = QPushButton("Discover")
        self.button_discover.clicked.connect(self.discover_devices)

        layout = QGridLayout()
        layout.addWidget(QLabel("IPv4 address:"), 0, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(QLabel("Port number:"), 1, 0, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.entry_ip, 0, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.entry_port, 1, 1, Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.button_discover, 3, 0, 1, 2, Qt.AlignmentFlag.AlignCenter)
        self.setLayout(layout)

    @pyqtSlot()
    def discover_devices(self):
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

        # even in multicast we treat the destination as a device, although serial and model number are meaningless
        device = Device("", "", QHostAddress(address), port)
        self.requested_discovery.emit(device, Command(CommandId.ID))

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
