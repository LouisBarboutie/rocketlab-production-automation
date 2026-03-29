import logging
import select
import socket
import struct
import threading

from PyQt5.QtCore import QObject, pyqtSlot

from codec import Codec, Command, CommandId

MULTICAST_ADDR = "224.3.11.15"
MULTICAST_PORT = 31115


class Server(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.codec = Codec()

    @pyqtSlot(str, int, CommandId)
    def command(self, address: str, port: int, command: CommandId):
        thread = threading.Thread(
            target=self.do_transaction,
            args=[address, port, Command[command.name]],
            daemon=True,
        )
        thread.start()

    def do_transaction(self, address: str, port: int, command: Command):
        logging.debug(f"Starting transaction for command {command.name}")
        data = self.codec.encode(command)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Bind to the multicast port so we can receive on it
        sock.bind(("localhost", 0))
        mreq = struct.pack("4sL", socket.inet_aton(MULTICAST_ADDR), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

        sock.sendto(data, (address, port))
        logging.info(f"Sent to {address}:{port} from socket {sock.getsockname()}")

        while True:
            ready = select.select([sock], [], [], 5)
            if ready[0]:
                data, device_address = sock.recvfrom(1024)
                decoded = self.codec.decode(data)
                logging.info(f"Received: {repr(decoded)} from {device_address}")

                # Both discover and test execution have a variable amount of responses
                if command in [Command.TEST_START, Command.ID]:
                    continue

                break

            logging.warning(
                f"Timed out while waiting for response from command {command.name} sent to {address}:{port}"
            )
            return

        logging.debug(f"Completed transaction for command {command.name}")
