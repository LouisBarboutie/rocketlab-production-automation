from dataclasses import dataclass


@dataclass
class Measurement:
    time: int
    milli_volts: float
    milli_amps: float
