import argparse
import datetime
import logging
import subprocess
import sys

from PyQt5.QtWidgets import QApplication

from mainwindow import MainWindow
from server import Server

parser = argparse.ArgumentParser()
parser.add_argument("-d", "--debug", action="store_true", default=False)
args = parser.parse_args()


class ColoredFormatter(logging.Formatter):
    colors = {
        logging.DEBUG: "\033[92m",
        logging.INFO: "\033[0m",
        logging.WARNING: "\033[93m",
        logging.ERROR: "\033[91m",
    }

    def format(self, record: logging.LogRecord):
        base_format = super().format(record)
        color = self.colors.get(record.levelno, "\033[0m")
        return f"{color}{base_format}\033[0m"


handler = logging.StreamHandler()
handler.setFormatter(
    ColoredFormatter(
        datefmt="%H:%M:%S", fmt="[{asctime}] {levelname:<8} - {message}", style="{"
    )
)

level = logging.DEBUG if args.debug else logging.INFO

logging.basicConfig(level=level, handlers=[handler])
try:
    version = subprocess.check_output(["git", "describe"], stderr=subprocess.DEVNULL)
except subprocess.CalledProcessError:
    version = subprocess.check_output(["git", "describe", "--always"])

logging.info(datetime.datetime.now().strftime(r"%a %d %B %Y"))
logging.info(f"Git revision {version.decode().strip()}")

app = QApplication(sys.argv)

server = Server()
window = MainWindow()

window.test_manager.relayed_command.connect(server.command)
window.test_manager.tab_closed.connect(server.command)
window.test_manager.interrupt.connect(server.interrupt)
window.discovery_box.requested_discovery.connect(server.command)

server.discovered_device.connect(window.selection_box.add_device)
server.received_measurement.connect(window.test_manager.relay_measurement)
server.finished_measurement.connect(window.test_manager.end_test)
server.detected_packet_loss.connect(window.test_manager.add_lost_packet)


window.show()

exit_code = app.exec()
logging.info(f"Application finished execution with exit code {exit_code}")

server.shutdown()


sys.exit(exit_code)
