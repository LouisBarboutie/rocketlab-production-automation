import logging
import select
import socket
import struct
import threading

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

from codec import Codec, CommandFormat, CommandId, EncodeError, DecodeError
from device import Device

MULTICAST_ADDR = "224.3.11.15"
MULTICAST_PORT = 31115


class Server(QObject):
    discovered_device = pyqtSignal(Device)

    def __init__(self) -> None:
        super().__init__()
        self.codec = Codec()

    @pyqtSlot(str, int, CommandId)
    def command(self, address: str, port: int, command: CommandId):
        thread = threading.Thread(
            target=self.do_transaction,
            args=[address, port, CommandFormat[command.name]],
            daemon=True,
        )
        thread.start()

    def do_transaction(self, address: str, port: int, command: CommandFormat):
        logging.debug(f"Starting transaction for command {command.name}")

        try:
            data = self.codec.encode(command)
        except EncodeError as error:
            logging.error(f"Failed to encode command: {error}")
            return

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind to the multicast port so we can receive on it
        sock.bind(("localhost", 0))
        mreq = struct.pack("4sL", socket.inet_aton(MULTICAST_ADDR), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        sock.sendto(data, (address, port))
        logging.info(f"Sent to {address}:{port} from socket {sock.getsockname()}")

        while True:
            ready = select.select([sock], [], [], 5)
            if not ready[0]:
                logging.warning(
                    f"Timed out while waiting for response from command {command.name} sent to {address}:{port}"
                )
                return

            data, device_address = sock.recvfrom(1024)
            try:
                response = self.codec.decode(data)
            except DecodeError as error:
                logging.error(f"Failed to decode response: {error}")
                continue

            logging.info(f"Received: {repr(response.raw)} from {device_address}")

            match command:
                case CommandFormat.TEST_STOP:
                    break
                case CommandFormat.TEST_START:
                    continue
                case CommandFormat.ID:
                    device = Device(
                        response.payload["model"],
                        response.payload["serial"],
                        *device_address,
                    )
                    self.discovered_device.emit(device)

        logging.debug(f"Completed transaction for command {command.name}")
