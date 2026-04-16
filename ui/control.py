import logging

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)

from ui.testparameters import TestParameters

MIN_TEST_DURATION_SECONDS = 0
MAX_TEST_DURATION_SECONDS = 3600
MIN_TEST_RATE_MILLISECONDS = 5  # Any lower than 3 might make the plots struggle


class ControlBox(QGroupBox):

    started_test = pyqtSignal(TestParameters)
    stopped_test = pyqtSignal()

    default_duration = 10
    default_rate = 10

    def __init__(self):
        super().__init__("Test control")

        self.entry_duration = QLineEdit()
        self.entry_duration.setValidator(QIntValidator())
        self.entry_duration.setText(str(ControlBox.default_duration))

        self.entry_rate = QLineEdit()
        self.entry_rate.setValidator(QIntValidator())
        self.entry_rate.setText(str(ControlBox.default_rate))

        self.lost_packets_count = 0
        self.lost_packets = QLineEdit()
        self.lost_packets.setReadOnly(True)
        self.lost_packets.setText(str(0))

        self.button_start = QPushButton("Start")
        self.button_stop = QPushButton("Stop")
        self.button_start.clicked.connect(self.start_test)
        self.button_stop.clicked.connect(self.stop_test)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Duration (s):"), 1, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.entry_duration, 1)
        layout.addWidget(QLabel("Rate (ms):"), 1, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.entry_rate, 1)
        layout.addWidget(QLabel("Packets lost:"), 1, Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.lost_packets, 1)
        layout.addWidget(self.button_start, 2)
        layout.addWidget(self.button_stop, 2)

        self.setLayout(layout)

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

        if not (text := self.entry_rate.text()):
            logging.debug("Missing test rate input")
            dialog = QMessageBox(self)
            dialog.setText(f"Please enter a test rate.")
            dialog.exec()
            return

        rate = int(text)
        if not MIN_TEST_RATE_MILLISECONDS < rate:
            logging.debug(f"Rate {rate} is not more than {MIN_TEST_RATE_MILLISECONDS}")
            dialog = QMessageBox(self)
            dialog.setText(
                f"Please enter a test rate above {MIN_TEST_RATE_MILLISECONDS} ms"
            )
            dialog.exec()
            return

        logging.info("Starting test!")

        self.set_input_lock(True)

        self.started_test.emit(TestParameters(duration, rate))

    @pyqtSlot()
    def stop_test(self) -> None:
        logging.info("Stopping test!")
        self.stopped_test.emit()
        self.end_test()

    @pyqtSlot()
    def end_test(self) -> None:
        logging.debug("Setting button states")
        self.set_input_lock(False)

    def add_lost_packet(self) -> None:
        self.lost_packets_count += 1
        self.lost_packets.setText(str(self.lost_packets_count))

    def set_input_lock(self, lock: bool) -> None:
        self.button_start.setEnabled(not lock)
        self.button_stop.setEnabled(lock)
        self.entry_duration.setReadOnly(lock)
        self.entry_rate.setReadOnly(lock)
