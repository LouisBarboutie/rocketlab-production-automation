import logging

from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

from codec import Command
from device import Device
from measurement import Measurement


class Worker(QObject):
    discovered_device = pyqtSignal(Device)
    received_measurement = pyqtSignal(Device, Measurement)
    finished = pyqtSignal(Device)
    detected_packet_loss = pyqtSignal(Device)
    error = pyqtSignal(Device)

    def __init__(self, device: Device, command: Command) -> None:
        super().__init__()
        self.device = device
        self.command = command
        self.should_stop = False

    @pyqtSlot()
    def work(self) -> None:
        try:
            while not self.should_stop:
                # add exchange via UDP
                pass
        except Exception as error:
            logging.error(f"Caught exception while trying to work: {error}")
            self.error.emit(self.device)
        finally:
            self.finished.emit(self.device)

    @pyqtSlot()
    def interrupt(self) -> None:
        logging.debug(f"Interrupting work for device {self.device}")
        self.should_stop = True
