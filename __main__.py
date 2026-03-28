import sys

from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtWidgets import (
    QApplication,
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


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.label_ip = QLabel()
        self.label_ip.setText("Target device IP:")
        self.entry_ip = QLineEdit()

        self.label_port = QLabel()
        self.label_port.setText("Target device port:")
        self.entry_port = QLineEdit()

        self.label_duration = QLabel()
        self.label_duration.setText("Test duration:")
        self.entry_duration = QLineEdit()

        self.button_start = QPushButton("Start")
        self.button_stop = QPushButton("Stop")
        self.button_start.clicked.connect(self.start_test)
        self.button_stop.clicked.connect(self.stop_test)

        params = QGridLayout()
        params.addWidget(self.label_ip, 0, 0, Qt.AlignmentFlag.AlignRight)
        params.addWidget(self.entry_ip, 0, 1, Qt.AlignmentFlag.AlignLeft)
        params.addWidget(self.label_port, 1, 0, Qt.AlignmentFlag.AlignRight)
        params.addWidget(self.entry_port, 1, 1, Qt.AlignmentFlag.AlignLeft)
        params.addWidget(self.label_duration, 2, 0, Qt.AlignmentFlag.AlignRight)
        params.addWidget(self.entry_duration, 2, 1, Qt.AlignmentFlag.AlignLeft)

        buttons = QVBoxLayout()
        buttons.addWidget(self.button_start)
        buttons.addWidget(self.button_stop)

        control_box = QGroupBox("Control")
        control_box.setLayout(buttons)

        param_box = QGroupBox("Parameters")
        param_box.setLayout(params)

        layout = QHBoxLayout()
        layout.addWidget(param_box)
        layout.addWidget(control_box)

        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    @pyqtSlot()
    def start_test(self):
        print("Starting test!")
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)

    @pyqtSlot()
    def stop_test(self):
        print("Stopping test!")
        self.button_start.setEnabled(True)
        self.button_stop.setEnabled(False)


app = QApplication([])

window = MainWindow()

window.setWindowTitle("RocketLab Production Automation Demo")

window.show()

sys.exit(app.exec())
