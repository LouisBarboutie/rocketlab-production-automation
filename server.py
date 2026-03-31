import logging
from functools import partial
from typing import Dict

from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot

from codec import Command
from device import Device
from measurement import Measurement
from worker import Worker


class Server(QObject):
    discovered_device = pyqtSignal(Device)
    received_measurement = pyqtSignal(Device, Measurement)
    finished_measurement = pyqtSignal(Device)
    detected_packet_loss = pyqtSignal(Device)
    error = pyqtSignal(Device)

    def __init__(self) -> None:
        super().__init__()
        self.threads: Dict[Device, QThread] = {}
        self.workers: Dict[Device, Worker] = {}

    @pyqtSlot(Device, Command)
    def command(self, device: Device, command: Command) -> None:
        if device in self.threads:
            return

        thread = QThread()
        worker = Worker(device, command)
        worker.moveToThread(thread)

        thread.started.connect(worker.work)

        # Cleanup chain to delete threads when worker is done (no reuse)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Threads don't know the device, so store it in a partial call
        thread.finished.connect(partial(self.cleanup, device))

        self.threads[device] = thread
        self.workers[device] = worker

        thread.start()

    @pyqtSlot(Device)
    def cleanup(self, device: Device) -> None:
        self.threads.pop(device, None)
        self.workers.pop(device, None)

    def shutdown(self) -> None:
        logging.debug(f"Shutting down workers")
        for worker in self.workers.values():
            worker.interrupt()
