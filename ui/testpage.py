from collections import deque
import logging
from typing import Deque

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from pyqtgraph import GraphicsLayoutWidget

from ui.control import ControlBox
from network.device import Device
from ui.measurement import Measurement


class TestPage(QWidget):

    started_test = pyqtSignal(Device, int, int)
    stopped_test = pyqtSignal(Device)

    def __init__(self, device: Device) -> None:
        super().__init__()
        self.device = device
        self.window_size_seconds = 10

        # If the entire history should be conserved
        # self.time: List[float] = []
        # self.voltages: List[float] = []
        # self.currents: List[float] = []

        # For performance reasons only keep the right amount of points to fit the window
        # Since deque length cannot be modified, they are created on test start
        self.plot_points = 100
        self.time: Deque[float]
        self.voltages: Deque[float]
        self.currents: Deque[float]

        self.plot_layout = GraphicsLayoutWidget()
        self.plot_voltage = self.plot_layout.addPlot(
            row=0,
            col=0,
            title=f"Voltage for model no. {self.device.model}, serial no. {self.device.serial}",
            labels={"bottom": "Elapsed time [s]", "left": "Voltage [mV]"},
        )
        self.plot_current = self.plot_layout.addPlot(
            row=1,
            col=0,
            title=f"Current for model no. {self.device.model}, serial no. {self.device.serial}",
            labels={"bottom": "Elapsed time [s]", "left": "Current [mA]"},
        )

        self.curve_voltage = self.plot_voltage.plot()
        self.curve_current = self.plot_current.plot()

        self.control_box = ControlBox()
        self.control_box.started_test.connect(self.start_test)
        self.control_box.stopped_test.connect(self.stop_test)

        layout = QVBoxLayout()
        layout.addWidget(self.control_box)
        layout.addWidget(self.plot_layout)
        self.setLayout(layout)

    def update_plots(self, measurement: Measurement) -> None:
        self.time.append(measurement.time / 1000)
        self.voltages.append(measurement.milli_volts)
        self.currents.append(measurement.milli_amps)

        if self.plot_layout.isVisible() is False:
            return

        self.curve_voltage.setData(self.time, self.voltages)
        self.curve_current.setData(self.time, self.currents)

        upper = self.time[-1]
        lower = upper - self.window_size_seconds

        if upper < self.window_size_seconds:
            upper = self.window_size_seconds
        if lower < 0:
            lower = 0

        self.plot_voltage.setXRange(lower, upper)
        self.plot_current.setXRange(lower, upper)

    def clear_plots(self) -> None:
        logging.debug("Clearing plot")

        self.curve_voltage.clear()
        self.curve_current.clear()
        self.plot_voltage.update()
        self.plot_current.update()

        # Not sure how to clear deques if they are recreated anyways
        # self.time.clear()
        # self.voltages.clear()
        # self.currents.clear()

    @pyqtSlot(int, int)
    def start_test(self, duration: int, rate: int) -> None:
        self.clear_plots()

        self.control_box.lost_packets_count = 0
        self.control_box.lost_packets.setText("0")
        self.control_box.set_input_lock(True)

        self.plot_points = int(self.window_size_seconds / rate * 1000)
        self.time = deque([], maxlen=self.plot_points)
        self.voltages = deque([], maxlen=self.plot_points)
        self.currents = deque([], maxlen=self.plot_points)

        logging.debug(f"Requested test start for {self.device}")
        self.started_test.emit(self.device, duration, rate)

    @pyqtSlot()
    def stop_test(self) -> None:
        logging.debug(f"Requested test stop for {self.device}")
        self.stopped_test.emit(self.device)

    def end_test(self) -> None:
        logging.debug("Test ended")
        # TODO maybe a pop up window to notify the user
        self.control_box.set_input_lock(False)

    def add_lost_packet(self):
        self.control_box.add_lost_packet()
