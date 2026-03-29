import argparse
import logging
import sys

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

from codec import Codec
from mainwindow import MainWindow

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


class QLogHandler(logging.Handler, QObject):
    appendLogMessage = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        QObject.__init__(self)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            message = self.format(record)
            self.appendLogMessage.emit(message)
        except RuntimeError:
            # Qt object deleted → ignore
            pass

    def close(self) -> None:
        """Remove the handler from logging and clean up QObject safely."""
        logger = logging.getLogger()
        if self in logger.handlers:
            logger.removeHandler(self)
        super().close()
        self.deleteLater()  # safely schedule QObject deletion


handler = logging.StreamHandler()
handler.setFormatter(
    ColoredFormatter(
        datefmt="%H:%M:%S", fmt="[{asctime}] {levelname:<8} - {message}", style="{"
    )
)
qhandler = QLogHandler()

level = logging.DEBUG if args.debug else logging.INFO

logging.basicConfig(level=level, handlers=[handler, qhandler])

app = QApplication(sys.argv)

window = MainWindow()
qhandler.appendLogMessage.connect(window.log.log)
window.show()

sys.exit(app.exec())
