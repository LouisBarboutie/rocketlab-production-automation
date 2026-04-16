import logging
from typing import Dict

from PyQt5.QtCore import pyqtSignal, pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QTabWidget

from network.codec import Command, CommandId
from network.device import Device
from ui.measurement import Measurement
from ui.testpage import TestPage
from ui.testparameters import TestParameters


class TestManager(QTabWidget):

    tab_closed = pyqtSignal(Device, Command)
    relayed_command = pyqtSignal(Device, Command)
    interrupt = pyqtSignal(Device)

    def __init__(self) -> None:
        super().__init__()
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.close_tab)
        self.tests: Dict[Device, TestPage] = {}

    @pyqtSlot(Device)
    def add_test(self, device: Device) -> None:
        if device in self.tests:
            logging.debug(f"Test already added for device {device}")
            dialog = QMessageBox(self)
            dialog.setText(f"Test already added for {device.serial}")
            dialog.exec()
            return

        page = TestPage(device)
        page.started_test.connect(self.start_test)
        page.stopped_test.connect(self.stop_test)
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
        else:
            # This case shouldn't be possible
            logging.error(f"Couldn't find test for device with serial no {serial}")
            return

        page = self.widget(index)
        page.started_test.disconnect()
        page.stopped_test.disconnect()

        logging.debug(f"Closing tab {serial}")
        self.removeTab(index)
        self.interrupt.emit(device)

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

    @pyqtSlot(Device, TestParameters)
    def start_test(self, device: Device, parameters: TestParameters):
        command = Command(CommandId.TEST_START)
        command.params["duration"] = parameters.duration
        command.params["rate"] = parameters.rate
        self.relayed_command.emit(device, command)

    @pyqtSlot(Device)
    def stop_test(self, device: Device):
        self.interrupt.emit(device)

    @pyqtSlot(Device)
    def end_test(self, device: Device) -> None:
        if device not in self.tests:
            logging.warning(
                f"Received end of test requeset from device {device} with no associated test"
            )
            return

        logging.debug(f"Ending test for device {device}")
        self.tests[device].end_test()

    @pyqtSlot(Device)
    def add_lost_packet(self, device: Device):
        if device not in self.tests:
            logging.warning(
                f"Received lost packet notification from {device} with no associated test"
            )
            return

        logging.warning(f"Lost packet for {device}")
        self.tests[device].add_lost_packet()
