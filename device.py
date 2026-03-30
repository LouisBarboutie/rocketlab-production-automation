from dataclasses import dataclass


@dataclass(frozen=True)
class Device:
    model: str
    serial: str
    address: str
    port: int
