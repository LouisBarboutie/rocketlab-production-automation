import logging
from dataclasses import dataclass
from functools import partial
from typing import Dict, Set

from PyQt5.QtCore import QMetaObject, QObject, QThread, pyqtSignal, pyqtSlot, Qt

from codec import Command, CommandId
from device import Device
from measurement import Measurement
from worker import Worker


@dataclass(frozen=True)
class Task:
    device: Device
    command: CommandId


class Server(QObject):
    discovered_device = pyqtSignal(Device)
    received_measurement = pyqtSignal(Device, Measurement)
    finished_measurement = pyqtSignal(Device)
    detected_packet_loss = pyqtSignal(Device)
    error = pyqtSignal(Device)

    def __init__(self) -> None:
        super().__init__()
        self.tasks: Set[Task] = set()
        self.threads: Dict[Task, QThread] = {}
        self.workers: Dict[Task, Worker] = {}

    @pyqtSlot(Device, Command)
    def command(self, device: Device, command: Command) -> None:
        logging.debug(f"Received {command} for {device}")
        task = Task(device, command.id)
        if task in self.tasks:
            logging.debug(f"{task} already running")
            return

        thread = QThread()
        worker = Worker(device, command)

        thread.started.connect(worker.work)

        worker.discovered_device.connect(self.discovered_device)
        worker.received_measurement.connect(self.received_measurement)
        # worker.finished.connect(self.finished_measurement)
        worker.detected_packet_loss.connect(self.detected_packet_loss)
        worker.error.connect(self.error)

        # Cleanup chain to delete threads when worker is done (no reuse)
        worker.finished.connect(self.remove_task)
        worker.finished.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)

        # Threads don't know the device, so store it in a partial call
        thread.finished.connect(partial(self.cleanup, task))

        self.tasks.add(task)
        self.threads[task] = thread
        self.workers[task] = worker

        worker.moveToThread(thread)
        thread.start()

    @pyqtSlot(Device)
    def interrupt(self, device: Device):
        logging.info(f"Interrupting worker for device {device}")
        to_stop = [task for task in self.tasks if task.device == device]

        for task in to_stop:
            self.tasks.discard(task)
            QMetaObject.invokeMethod(
                self.workers[task], "interrupt", Qt.ConnectionType.QueuedConnection
            )

    @pyqtSlot(Task)
    def cleanup(self, task: Task) -> None:
        logging.debug(f"Cleaning up {task}")
        self.tasks.discard(task)
        self.threads.pop(task, None)
        self.workers.pop(task, None)

    def remove_task(self, device: Device, command: Command):
        task = Task(device, command.id)
        logging.debug(f"Discarding {task}")
        self.tasks.discard(task)

    def shutdown(self) -> None:
        logging.debug(f"Shutting down workers")
        tasks = self.tasks.copy()
        for task in tasks:
            self.interrupt(task.device)

        for task, thread in self.threads.items():
            logging.debug(f"Stopping thread for {task}")
            thread.quit()
            thread.wait()
