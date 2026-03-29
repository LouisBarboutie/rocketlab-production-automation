from dataclasses import dataclass, field
from enum import StrEnum, IntEnum
from typing import Dict, Any, Optional
import logging
import re

from PyQt5.QtCore import QObject, pyqtSignal

# TODO Clean these enums up, maybe wrap them into dicts in the init. The only remaining enum should be CommandId


class CommandId(IntEnum):
    """Command identifiers to be emitted by PyQt signals."""

    ID = 0
    TEST_START = 1
    TEST_STOP = 2


class CommandFormat(StrEnum):
    """Command format templates to be completed by the encoder."""

    ID = "ID;"
    TEST_START = "TEST;CMD=START;DURATION={duration};RATE={rate};"
    TEST_STOP = "TEST;CMD=STOP;"


class ResponseFormat(StrEnum):
    """Response format templates to be matched by the decoder."""

    ID = r"ID;MODEL=(\w+);SERIAL=(\w+);"
    TEST_START = r"TEST;RESULT=STARTED;"
    TEST_STOP = r"TEST;RESULT=STOPPED;"
    TEST_ERR = r"TEST;RESULT=(\w+);MSG=([^;]+);"
    STATUS_MEASURE = r"STATUS;TIME=(\d+);MV=([+-]?[\d.]+);MA=([+-]?[\d.]+);"
    STATUS_STATE = r"STATUS;STATE=IDLE;"
    ERROR = r"ERR;REASON=([^;]+);"


@dataclass
class Response:
    raw: str
    payload: Dict[str, Any] = field(init=False, default_factory=dict)


class EncodeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class DecodeError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class Codec(QObject):

    decoded_id = pyqtSignal(str, str)
    test_started = pyqtSignal()
    test_stopped = pyqtSignal()
    test_error = pyqtSignal()
    measurement = pyqtSignal(int, float, float)

    def __init__(self) -> None:
        super().__init__()
        self.encoding = "iso-8859-1"
        self.patterns = {entry: re.compile(entry.value) for entry in ResponseFormat}

    def encode(self, command: CommandFormat, duration: int = 10, rate=1000) -> bytes:
        match command:
            case CommandFormat.ID | CommandFormat.TEST_STOP:
                for_sending = command.value
            case CommandFormat.TEST_START:
                for_sending = command.value.format(duration=duration, rate=rate)
            case _:
                raise EncodeError("Unknown command")

        logging.debug(f"Built command {repr(for_sending)}")
        return for_sending.encode(self.encoding)

    def decode(self, data: bytes) -> Response:
        decoded = data.decode(self.encoding)

        logging.debug(f"Decoding data {repr(decoded)}")

        for key, pattern in self.patterns.items():
            m = pattern.fullmatch(decoded)
            if m is not None:
                logging.debug(f"Matched response format for response {key.name}")
                break
        else:
            raise DecodeError("Unknown response format")

        response = Response(decoded)
        match key:
            case ResponseFormat.ID:
                response.payload["model"] = m.group(1)
                response.payload["serial"] = m.group(2)
            case (
                ResponseFormat.TEST_START
                | ResponseFormat.TEST_STOP
                | ResponseFormat.STATUS_STATE
            ):
                pass
            case ResponseFormat.TEST_ERR | ResponseFormat.ERROR:
                response.payload["error"] = m.group(1)
            case ResponseFormat.STATUS_MEASURE:
                try:
                    response.payload["t"] = int(m.group(1))
                    response.payload["mv"] = float(m.group(2))
                    response.payload["ma"] = float(m.group(3))
                except ValueError:
                    raise DecodeError(
                        f"Couldn't convert measurements to numeric: time={m.group(1)}, mv={m.group(2)}, ma={m.group(3)}"
                    )

        return response
