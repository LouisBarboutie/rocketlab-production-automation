import logging
import select
import socket
import struct
import threading
from typing import Dict, Tuple

from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

from codec import (
    Codec,
    Command,
    CommandId,
    DeviceError,
    EncodeError,
    DecodeError,
    ResponseId,
)
from device import Device
from measurement import Measurement
from testpage import DEFAULT_RATE_MILLISECONDS

MULTICAST_ADDR = "224.3.11.15"
MULTICAST_PORT = 31115
MIN_TIMEOUT_SECONDS = 5


class Server(QObject):
    discovered_device = pyqtSignal(Device)
    received_measurement = pyqtSignal(Device, Measurement)
    finished_measurement = pyqtSignal(Device)
    detected_packet_loss = pyqtSignal(Device)

    def __init__(self) -> None:
        super().__init__()
        self.codec = Codec()
        self.discovered_devices: Dict[Tuple[str, int], Device] = {}

    @pyqtSlot(Device, Command)
    def command(self, device: Device, command: Command):
        thread = threading.Thread(
            target=self.do_transaction,
            args=[device.address, device.port, command],
            daemon=True,
        )
        thread.start()

    def do_transaction(self, address: str, port: int, command: Command):
        logging.debug(f"Starting transaction for command {command.id.name}")

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

        timeout = command.params.get("duration", 0) + MIN_TIMEOUT_SECONDS
        logging.debug(f"Setting timeout to {timeout} seconds")
        last_packet_time = 0

        while True:
            ready = select.select([sock], [], [], timeout)
            if not ready[0]:
                logging.warning(
                    f"Timed out while waiting for response from command {command.id.name} sent to {address}:{port}"
                )
                return

            data, device_address = sock.recvfrom(1024)
            try:
                response = self.codec.decode(data)
            except DecodeError as error:
                logging.error(f"Failed to decode response: {error}")
                continue
            except DeviceError as error:
                logging.error(f"Device returned an unrecoverable error, aborting")
                return

            logging.info(
                f"Received: {repr(response.raw)} (ID={response.id}) from {device_address}"
            )

            match command.id:
                case CommandId.TEST_STOP:
                    break
                case CommandId.TEST_START:
                    if response.id == ResponseId.STATUS_MEASURE:
                        expected_time = last_packet_time + DEFAULT_RATE_MILLISECONDS
                        if response.payload["t"] != expected_time:
                            logging.warning(
                                f"Packet loss detected for timestamp {expected_time}"
                            )
                            self.detected_packet_loss.emit(
                                self.discovered_devices[device_address]
                            )
                        last_packet_time = response.payload["t"]

                        self.received_measurement.emit(
                            self.discovered_devices[device_address],
                            Measurement(
                                response.payload["t"],
                                response.payload["mv"],
                                response.payload["ma"],
                            ),
                        )
                        continue

                    if response.id == ResponseId.STATUS_STATE:
                        self.finished_measurement.emit(
                            self.discovered_devices[device_address]
                        )
                        return
                case CommandId.ID:
                    device = Device(
                        response.payload["model"],
                        response.payload["serial"],
                        *device_address,
                    )
                    self.discovered_devices[device_address] = device
                    self.discovered_device.emit(device)
                case _:
                    logging.error(f"Command '{command}' not recognised!")

        logging.debug(f"Completed transaction for command {command.id.name}")
