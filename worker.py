import logging

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot
from PyQt5.QtNetwork import QHostAddress, QUdpSocket

from codec import Command, Codec, ResponseId, CommandId
from device import Device
from measurement import Measurement

MULTICAST_ADDR = "224.3.11.15"
MULTICAST_PORT = 31115
MIN_TIMEOUT_MILLI_SECONDS = 5000


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

        self.codec = Codec()
        self.socket: QUdpSocket
        self.timer: QTimer

    @pyqtSlot()
    def work(self) -> None:
        self.create_socket()
        self.send_command(self.command)

    @pyqtSlot()
    def interrupt(self) -> None:
        logging.debug(f"Interrupting work for device {self.device}")
        self.send_command(Command(CommandId.TEST_STOP))

        self.socket.readyRead.disconnect(self.process_response)
        self.timer.timeout.disconnect(self.interrupt)
        self.socket.close()
        self.socket.deleteLater()

    @pyqtSlot()
    def process_response(self) -> None:
        while self.socket.hasPendingDatagrams():
            size = self.socket.pendingDatagramSize()
            data, address, port = self.socket.readDatagram(size)
            logging.debug(f"Received from {address}:{port} data {data}")
            response = self.codec.decode(data)

            match response.id:
                case ResponseId.ID:
                    self.discovered_device.emit(
                        Device(
                            response.payload["model"],
                            response.payload["serial"],
                            address,
                            port,
                        )
                    )
                    self.finished.emit(self.device)
                case ResponseId.STATUS_MEASURE:
                    # TODO check packet loss
                    self.received_measurement.emit(
                        self.device,
                        Measurement(
                            response.payload["t"],
                            response.payload["mv"],
                            response.payload["ma"],
                        ),
                    )
                    self.timer.start()
                case ResponseId.STATUS_STATE:
                    self.finished.emit(self.device)
                case ResponseId.ERROR | ResponseId.TEST_ERR:
                    self.error.emit(self.device)
                case ResponseId.TEST_START:
                    pass
                case _:
                    logging.warning(f"Unkown response id: {response.id}")

    def create_socket(self) -> None:
        """
        Creates the socket from within the thread the worker is currently in.
        If not created and connected in the same thread, signal and slots won't work.
        """
        self.timer = QTimer()
        self.timer.setInterval(MIN_TIMEOUT_MILLI_SECONDS)
        self.timer.timeout.connect(self.interrupt)

        self.socket = QUdpSocket()
        self.socket.bind(QHostAddress.SpecialAddress.AnyIPv4)
        self.socket.joinMulticastGroup(QHostAddress(MULTICAST_ADDR))
        self.socket.readyRead.connect(self.process_response)

        logging.debug(
            f"Bound port on address {self.socket.localAddress().toString()}, port {self.socket.localPort()}"
        )

    def send_command(self, command: Command) -> None:
        encoded = self.codec.encode(command)
        logging.debug(f"Sending command to {self.device}")
        self.socket.writeDatagram(encoded, self.device.address, self.device.port)
        self.timer.start()
