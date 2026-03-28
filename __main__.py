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
from pyqtgraph import PlotWidget, PlotItem
import numpy as np


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

    @pyqtSlot()
    def start_test(self):
        print("Starting test!")
        self.button_start.setEnabled(False)
        self.button_stop.setEnabled(True)
        self.xdata += 1
        self.ydata = np.sin(self.xdata)
        self.plot_item.items[0].setData(self.xdata, self.ydata)

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
