import logging
from typing import Dict

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QTabWidget

from codec import Command
from device import Device
from measurement import Measurement
from testpage import TestPage


class TestManager(QTabWidget):

    tab_closed = pyqtSignal(Device)
    relayed_command = pyqtSignal(Device, Command)

    def __init__(self) -> None:
        super().__init__()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.tests: Dict[Device, TestPage] = {}

    @pyqtSlot(Device)
    def add_test(self, device: Device) -> None:
        if device in self.tests:
            logging.debug(f"Test already added for device {device}")
            return

        page = TestPage(device)
        page.started_test.connect(self.relay_command)
        page.stopped_test.connect(self.relay_command)
        self.tests[device] = page

        index = self.addTab(page, device.serial)
        self.setCurrentIndex(index)
        logging.debug(f"Added test for device {device}")

    @pyqtSlot(int)
    def close_tab(self, index: int) -> None:
        serial = self.tabText(index)

        for device in self.tests:
            if device.serial == serial:
                self.tests.pop(device)
                break

        page = self.widget(index)
        page.started_test.disconnect()
        page.stopped_test.disconnect()

        logging.debug(f"Closing tab {serial}")
        self.removeTab(index)
        self.tab_closed.emit(device)

    @pyqtSlot(Device, Command)
    def relay_command(self, device: Device, command: Command) -> None:
        logging.debug(f"Relaying command for device {device}: {command}")
        self.relayed_command.emit(device, command)

    @pyqtSlot(Device, Measurement)
    def relay_measurement(self, device: Device, measurement: Measurement) -> None:
        if device not in self.tests:
            logging.warning(
                f"Received measurement from device {device} with no associated test"
            )
            return

        logging.debug(f"Relaying measurement for device {device}: {measurement}")
        self.tests[device].update_plots(measurement)

    @pyqtSlot(Device)
    def end_test(self, device: Device) -> None:
        if device not in self.tests:
            logging.warning(
                f"Received end of test requeset from device {device} with no associated test"
            )
            return

        logging.debug(f"Ending test for device {device}")
        self.tests[device].end_test()
