import logging
from typing import List

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from pyqtgraph import PlotItem, PlotWidget

from codec import Command, CommandId
from control import ControlBox
from device import Device
from measurement import Measurement


class TestPage(QWidget):

    started_test = pyqtSignal(Device, Command)
    stopped_test = pyqtSignal(Device, Command)

    def __init__(self, device: Device) -> None:
        super().__init__()
        self.device = device
        self.window_size_seconds = 10

        self.time: List[float] = []
        self.voltages: List[float] = []
        self.currents: List[float] = []

        plot_item_voltage = PlotItem(
            title=f"Voltage for model no. {self.device.model}, serial no. {self.device.serial}",
            labels={"bottom": "Elapsed time [s]", "left": "Voltage [mV]"},
        )
        plot_item_current = PlotItem(
            title=f"Current for model no. {self.device.model}, serial no. {self.device.serial}",
            labels={"bottom": "Elapsed time [s]", "left": "Current [mA]"},
        )

        self.plot_voltage = PlotWidget(plotItem=plot_item_voltage)
        self.plot_current = PlotWidget(plotItem=plot_item_current)

        self.curve_voltage = plot_item_voltage.plot()
        self.curve_current = plot_item_current.plot()

        self.control_box = ControlBox()
        self.control_box.started_test.connect(self.start_test)
        self.control_box.stopped_test.connect(self.stop_test)

        layout = QVBoxLayout()
        layout.addWidget(self.control_box)
        layout.addWidget(self.plot_voltage)
        layout.addWidget(self.plot_current)
        self.setLayout(layout)

    def update_plots(self, measurement: Measurement) -> None:
        self.time.append(measurement.time / 1000)
        self.voltages.append(measurement.milli_volts)
        self.currents.append(measurement.milli_amps)

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

        self.time.clear()
        self.voltages.clear()
        self.currents.clear()

    @pyqtSlot(int)
    def start_test(self, duration: int) -> None:
        logging.debug(f"Requested test start for {self.device}")
        command = Command(CommandId.TEST_START)
        command.params["duration"] = duration
        self.clear_plots()
        self.started_test.emit(self.device, command)

    @pyqtSlot()
    def stop_test(self) -> None:
        logging.debug(f"Requested test stop for {self.device}")
        self.stopped_test.emit(self.device, Command(CommandId.TEST_STOP))

    def end_test(self) -> None:
        logging.debug("Test ended")
        # TODO maybe a pop up window to notify the user
