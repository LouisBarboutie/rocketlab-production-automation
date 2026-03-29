from dataclasses import dataclass


@dataclass
class Device:
    model: str
    serial: str
    address: str
    port: int
