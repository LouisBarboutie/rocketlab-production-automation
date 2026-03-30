import logging

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIntValidator
from PyQt5.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QMessageBox,
)

MIN_TEST_DURATION_SECONDS = 0
MAX_TEST_DURATION_SECONDS = 3600


class ControlBox(QGroupBox):

    started_test = pyqtSignal(int)
    stopped_test = pyqtSignal()

    default_duration = 10

    def __init__(self):
        super().__init__("Test control")

        self.entry_duration = QLineEdit()
        self.entry_duration.setValidator(QIntValidator())
        self.entry_duration.setText(str(ControlBox.default_duration))

        self.button_start = QPushButton("Start")
        self.button_stop = QPushButton("Stop")
        self.button_start.clicked.connect(self.start_test)
        self.button_stop.clicked.connect(self.stop_test)

        layout = QHBoxLayout()
        layout.addWidget(QLabel("Test duration:"), 1)
        layout.addWidget(self.entry_duration, 1)
        layout.addWidget(self.button_start, 1)
        layout.addWidget(self.button_stop, 1)

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

        logging.info("Starting test!")

        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)

        self.started_test.emit(duration)

    @pyqtSlot()
    def stop_test(self) -> None:
        logging.info("Stopping test!")
        self.stopped_test.emit()
        self.end_test()

    @pyqtSlot()
    def end_test(self) -> None:
        logging.debug("Setting button states")
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)
