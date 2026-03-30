import logging
from typing import List, Dict, Tuple

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QWidget, QVBoxLayout, QMessageBox
from pyqtgraph import PlotItem, PlotWidget

from device import Device
from measurement import Measurement


class PlotTabs(QTabWidget):

    tab_closed = pyqtSignal(Device)

    def __init__(self) -> None:
        super().__init__()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)

        self.time: List[float] = []
        self.milli_volts: List[float] = []
        self.milli_amps: List[float] = []
        self.window_size_seconds = 10

        self.plot_widgets: Dict[str, Tuple[PlotWidget, PlotWidget]] = {}

    @pyqtSlot(Device)
    def add_test(self, device: Device) -> bool:
        if device.serial in self.plot_widgets:
            logging.debug(f"Test already added for device {device}")
            return False

        plot_item_voltage = PlotItem(
            title=f"Voltage for model no. {device.model}, serial no. {device.serial}",
            labels={"bottom": "Elapsed time [s]", "left": "Voltage [mV]"},
        )
        plot_item_current = PlotItem(
            title=f"Current for model no. {device.model}, serial no. {device.serial}",
            labels={"bottom": "Elapsed time [s]", "left": "Current [mA]"},
        )
        plot_voltage = PlotWidget(plotItem=plot_item_voltage)
        plot_current = PlotWidget(plotItem=plot_item_current)

        self.curve_voltage = plot_item_voltage.plot()
        self.curve_current = plot_item_current.plot()

        page = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(plot_voltage)
        layout.addWidget(plot_current)
        page.setLayout(layout)

        self.plot_widgets[device.serial] = (plot_voltage, plot_current)

        index = self.addTab(page, device.serial)
        self.setCurrentIndex(index)
        logging.debug(f"Added test for device {device}")

        return True

    @pyqtSlot(Device, Measurement)
    def update_plot(self, device: Device, measurement: Measurement) -> None:
        if device.serial not in self.plot_widgets:
            return

        self.time.append(measurement.time / 1000)
        self.milli_volts.append(measurement.milli_volts)
        self.milli_amps.append(measurement.milli_amps)

        self.curve_voltage.setData(self.time, self.milli_volts)
        self.curve_current.setData(self.time, self.milli_amps)

        upper = self.time[-1]
        lower = upper - self.window_size_seconds

        if upper < self.window_size_seconds:
            upper = self.window_size_seconds
        if lower < 0:
            lower = 0

        self.plot_widgets[device.serial][0].setXRange(lower, upper)
        self.plot_widgets[device.serial][1].setXRange(lower, upper)

    @pyqtSlot(Device)
    def clear_plot(self, device: Device) -> None:
        logging.debug("Clearing plot")

        self.curve_voltage.clear()
        self.curve_current.clear()
        self.plot_widgets[device.serial][0].update()
        self.plot_widgets[device.serial][1].update()

        self.time.clear()
        self.milli_volts.clear()
        self.milli_amps.clear()

    @pyqtSlot(int)
    def close_tab(self, index: int):
        serial = self.tabText(index)
        device = Device("", serial, "", 0)
        self.clear_plot(device)

        self.plot_widgets.pop(serial)

        logging.debug(f"Closing tab {serial}")
        self.removeTab(index)
        self.tab_closed.emit(device)
