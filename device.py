from dataclasses import dataclass

from PyQt5.QtNetwork import QHostAddress


@dataclass(frozen=True)
class Device:
    model: str
    serial: str
    address: QHostAddress
    port: int
