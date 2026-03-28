from enum import Enum, StrEnum
import re
from string import Template

from PyQt5.QtCore import QObject, pyqtSignal


class Command(StrEnum):
    ID = "ID;"
    TEST_START = "TEST;CMD=START;DURATION={duration};RATE={rate};"
    TEST_STOP = "TEST;CMD=STOP;"


class Response(StrEnum):
    ID = r"ID;MODEL=(\w+);SERIAL=(\w+);"
    TEST_START = r"TEST;RESULT=STARTED;"
    TEST_STOP = r"TEST;RESULT=STOPPED;"
    TEST_ERR = r"TEST;RESULT=(\w+);MSG=(\w+);"
    STATUS_MEASURE = r"STATUS;TIME=(\d+);MV=([+-]?[\d.]+);MA=([+-]?[\d.]+);"
    STATUS_STATE = r"STATUS;STATE=IDLE"


class Codec(QObject):

    decoded_id = pyqtSignal(str, str)
    test_started = pyqtSignal()
    test_stopped = pyqtSignal()
    test_error = pyqtSignal()
    measurement = pyqtSignal(int, float, float)

    def __init__(self) -> None:
        super().__init__()
        self.encoding = "iso-8859-1"
        self.patterns = {entry: re.compile(entry.value) for entry in Response}

    def encode(self, command: Command, duration: int = 0, rate=1000) -> bytes:
        match command:
            case Command.ID | Command.TEST_STOP:
                for_sending = command.value
            case Command.TEST_START:
                for_sending = command.value.format(duration=duration, rate=rate)
            case _:
                print("Unknown command")

        print(f"Encoded: {for_sending}")
        return for_sending.encode(self.encoding)

    def decode(self, data: bytes) -> None:
        decoded = data.decode(self.encoding)

        for key, pattern in self.patterns.items():
            m = pattern.fullmatch(decoded)
            if m is not None:
                break
        else:
            print("Unknown response format!")

        match key:
            case Response.ID:
                self.decoded_id.emit(m.group(1), m.group(2))
            case Response.TEST_START:
                self.test_started.emit()
            case Response.TEST_STOP:
                self.test_stopped.emit()
            case Response.TEST_ERR:
                self.test_error.emit()
            case Response.STATUS_MEASURE:
                try:
                    time = int(m.group(1))
                    milli_volt = float(m.group(2))
                    milli_amps = float(m.group(3))
                except ValueError as error:
                    print(
                        f"Couldn't convert measurements to numeric: time={m.group(1)}, mv={m.group(2)}, ma={m.group(3)}",
                        error,
                        sep="\n",
                    )
                    return
                self.measurement.emit(time, milli_volt, milli_amps)
            case Response.STATUS_STATE:
                pass


if __name__ == "__main__":
    s = "ID;MODEL=;SERIAL=;"
    pattern = re.compile(Response["ID"])
    m = pattern.fullmatch(s)
    if m is not None:
        print(m.group(1), m.group(2))

    codec = Codec()

    s = "STTUS;TIME=1000;MV=4471.6;MA=38.3;"
    codec.decode(s.encode(codec.encoding))
    codec.encode(Command.TEST_START, 10)
