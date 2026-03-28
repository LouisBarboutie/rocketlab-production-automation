import logging
import ipaddress

from PyQt5.QtGui import QIntValidator
import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QHBoxLayout,
    QMainWindow,
    QLineEdit,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QGridLayout,
    QGroupBox,
)
from pyqtgraph import PlotWidget, PlotItem

MIN_PORT_NUMBER = 0
MAX_PORT_NUMBER = 65535

MIN_TEST_DURATION_SECONDS = 0
MAX_TEST_DURATION_SECONDS = 3600


class MainWindow(QMainWindow):

    selected_device = pyqtSignal(str, int)

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("RocketLab Production Automation Demo")

        self.label_ip = QLabel()
        self.label_ip.setText("Target device IP:")
        self.entry_ip = QLineEdit()

        self.label_port = QLabel()
        self.label_port.setText("Target device port:")
        self.entry_port = QLineEdit()
        self.entry_port.setValidator(QIntValidator())

        self.label_duration = QLabel()
        self.label_duration.setText("Test duration:")
        self.entry_duration = QLineEdit()
        self.entry_duration.setValidator(QIntValidator())

        self.button_select = QPushButton("Select")
        self.button_start = QPushButton("Start")
        self.button_stop = QPushButton("Stop")
        self.button_select.clicked.connect(self.select_device)
        self.button_start.clicked.connect(self.start_test)
        self.button_stop.clicked.connect(self.stop_test)

        self.plot_item = PlotItem(title="Test Plot")
        self.plot_item.setLabel("bottom", "time [s]")
        self.plot_item.setLabel("left", "Value [a.u.]")

        self.xdata = np.linspace(0, 20, 100)
        self.ydata = np.zeros_like(self.xdata)
        self.plot_item.plot(self.xdata, self.ydata)
        self.plot_widget = PlotWidget(plotItem=self.plot_item)

        params = QGridLayout()
        params.addWidget(self.label_ip, 0, 0, Qt.AlignmentFlag.AlignRight)
        params.addWidget(self.entry_ip, 0, 1, Qt.AlignmentFlag.AlignLeft)
        params.addWidget(self.label_port, 1, 0, Qt.AlignmentFlag.AlignRight)
        params.addWidget(self.entry_port, 1, 1, Qt.AlignmentFlag.AlignLeft)
        params.addWidget(self.label_duration, 2, 0, Qt.AlignmentFlag.AlignRight)
        params.addWidget(self.entry_duration, 2, 1, Qt.AlignmentFlag.AlignLeft)

        buttons = QVBoxLayout()
        buttons.addWidget(self.button_select)
        buttons.addWidget(self.button_start)
        buttons.addWidget(self.button_stop)

        control_box = QGroupBox("Control")
        control_box.setLayout(buttons)

        param_box = QGroupBox("Parameters")
        param_box.setLayout(params)

        layout = QHBoxLayout()
        layout.addWidget(param_box)
        layout.addWidget(control_box)
        layout.addWidget(self.plot_widget)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def start_test(self):
        if not (text := self.entry_duration.text()):
            return

        duration = int(text)
        if not MIN_TEST_DURATION_SECONDS <= duration <= MAX_TEST_DURATION_SECONDS:
            logging.debug(
                f"Duration '{self.entry_duration.text()}' is not within the range [{MIN_TEST_DURATION_SECONDS}, {MAX_TEST_DURATION_SECONDS}] seconds"
            )
            return

        logging.info("Starting test!")
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.xdata += 1
        self.ydata = np.sin(self.xdata)
        self.plot_item.items[0].setData(self.xdata, self.ydata)

    def stop_test(self):
        logging.info("Stopping test!")
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)

    def select_device(self):
        address = self.entry_ip.text()
        if not self.is_valid_ipv4(address):
            logging.debug(f"Address '{address}' is not a valid IPv4 address!")
            return

        if not (text := self.entry_port.text()):
            return

        port = int(text)
        if not MIN_PORT_NUMBER <= port <= MAX_PORT_NUMBER:
            logging.debug(f"Port '{port}' is not a valid port number!")
            return

        logging.debug(f"Selected device on {address}:{port}")
        self.selected_device.emit(address, port)

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
