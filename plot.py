import logging
from typing import List, Dict

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QMessageBox
from pyqtgraph import PlotItem, PlotWidget

from device import Device
from measurement import Measurement


class PlotTabs(QTabWidget):
    def __init__(self) -> None:
        super().__init__()

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

        self.test_index: Dict[str, int] = {}

    def add_test(self, device: Device) -> bool:
        if device.serial in self.test_index:
            return False

        plot_item = PlotItem(
            title=f"Test for model no. {device.model}, serial no. {device.serial} "
        )
        plot = PlotWidget(plotItem=plot_item)
        page = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(plot)
        page.setLayout(layout)
        self.test_index[device.serial] = self.addTab(page, device.serial)

        return True

    @pyqtSlot(Measurement)
    def update_plot(self, measurement: Measurement) -> None:
        self.time.append(measurement.time / 1000)
        self.milli_volts.append(measurement.milli_volts)
        self.milli_amps.append(measurement.milli_amps)

        self.curve_volts.setData(self.time, self.milli_volts)
        self.curve_amps.setData(self.time, self.milli_amps)

        upper = self.time[-1]
        lower = upper - self.window_size_seconds

        if upper < self.window_size_seconds:
            upper = self.window_size_seconds
        if lower < 0:
            lower = 0

        self.plot_widget.setXRange(lower, upper)

    @pyqtSlot()
    def clear(self) -> None:
        logging.debug("Clearing plot")

        self.curve_volts.clear()
        self.curve_amps.clear()
        self.plot_item.update()

        self.time.clear()
        self.milli_volts.clear()
        self.milli_amps.clear()
