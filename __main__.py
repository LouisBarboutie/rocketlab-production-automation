import argparse
import logging
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

app = QApplication(sys.argv)

server = Server()
window = MainWindow()

window.started_test.connect(server.command)
window.stopped_test.connect(server.command)
window.discovery_box.requested_discovery.connect(server.command)

server.discovered_device.connect(window.add_device)
server.received_measurement.connect(window.update_plot)
server.finished_measurement.connect(window.stop_test)

window.show()
sys.exit(app.exec())
