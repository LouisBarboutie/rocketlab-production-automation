import logging

from PyQt5.QtCore import QObject, QTimer, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtNetwork import QHostAddress, QUdpSocket

from network.codec import Command, Codec, ResponseId, CommandId
from network.device import Device
from ui.measurement import Measurement

MULTICAST_ADDR = "224.3.11.15"
MULTICAST_PORT = 31115
MIN_TIMEOUT_MILLI_SECONDS = 5000


class Worker(QObject):
    discovered_device = pyqtSignal(Device)
    received_measurement = pyqtSignal(Device, Measurement)
    finished = pyqtSignal(Device, Command)
    detected_packet_loss = pyqtSignal(Device)
    error = pyqtSignal(Device)

    def __init__(self, device: Device, command: Command) -> None:
        super().__init__()
        self.device = device
        self.command = command
        self.should_stop = False

        self.codec = Codec()
        self.socket: QUdpSocket

        self.last_packet_time: int = 0
        self.expected_delay: int = command.params.get("rate", 0)

    @pyqtSlot()
    def work(self) -> None:
        self.create_socket()
        self.send_command(self.command)

    @pyqtSlot()
    def interrupt(self) -> None:
        logging.debug(f"Interrupting work for device {self.device}")
        self.send_command(Command(CommandId.TEST_STOP))

        # self.socket.readyRead.disconnect(self.process_response)
        # self.socket.close()
        # self.socket.deleteLater()
        #
        # self.finished.emit(self.device)

    @pyqtSlot()
    def process_response(self) -> None:
        while self.socket.hasPendingDatagrams():
            size = self.socket.pendingDatagramSize()
            data, address, port = self.socket.readDatagram(size)
            logging.debug(f"Received from {address}:{port} data {data}")

            try:
                response = self.codec.decode(data)
            except Exception as error:
                logging.error(f"Something went wrong while decoding: {error}")
                return

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
                    self.finished.emit(self.device, self.command)
                case ResponseId.STATUS_MEASURE:
                    expected_time = self.last_packet_time + self.expected_delay
                    if response.payload["t"] != expected_time:
                        logging.warning(
                            f"Packet loss detected for timestamp {expected_time}"
                        )
                        self.detected_packet_loss.emit(self.device)
                    self.last_packet_time = response.payload["t"]

                    self.received_measurement.emit(
                        self.device,
                        Measurement(
                            response.payload["t"],
                            response.payload["mv"],
                            response.payload["ma"],
                        ),
                    )
                case ResponseId.STATUS_STATE | ResponseId.TEST_STOP:
                    self.finished.emit(self.device, self.command)
                case ResponseId.ERROR | ResponseId.TEST_ERR:
                    self.finished.emit(self.device, self.command)
                case ResponseId.TEST_START:
                    pass
                case _:
                    logging.warning(f"Unkown response id: {response.id}")
                    self.error.emit(self.device)
                    self.finished.emit(self.device, self.command)

    def create_socket(self) -> None:
        """
        Creates the socket from within the thread the worker is currently in.
        If not created and connected in the same thread, signal and slots won't work.
        """

        self.socket = QUdpSocket()
        self.socket.bind(QHostAddress.SpecialAddress.AnyIPv4)
        self.socket.joinMulticastGroup(QHostAddress(MULTICAST_ADDR))
        self.socket.readyRead.connect(self.process_response)

        logging.debug(
            f"Bound port on address {self.socket.localAddress().toString()}, port {self.socket.localPort()}"
        )

    def send_command(self, command: Command) -> None:
        try:
            encoded = self.codec.encode(command)
        except Exception as error:
            logging.error(f"Something went wrong while encoding: {error}")
            return

        logging.debug(f"Sending command to {self.device}")
        self.socket.writeDatagram(encoded, self.device.address, self.device.port)
