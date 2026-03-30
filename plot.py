import logging
from typing import List

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QTabWidget, QWidget, QHBoxLayout, QLabel
from pyqtgraph import PlotItem, PlotWidget


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

        self.addTab(QWidget(), "The page")
        page = QWidget()
        layout = QHBoxLayout()
        layout.addWidget(QLabel("Boo"))
        page.setLayout(layout)
        self.addTab(page, "The cooler page")
        self.addTab(self.plot_widget, "plot")

    @pyqtSlot(int, float, float)
    def update_plot(self, time: int, milli_volts: float, milli_amps: float) -> None:
        self.time.append(time / 1000)
        self.milli_volts.append(milli_volts)
        self.milli_amps.append(milli_amps)

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
