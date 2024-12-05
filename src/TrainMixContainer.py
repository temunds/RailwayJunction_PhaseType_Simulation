
from dataclasses import dataclass


@dataclass
class TrainMixContainer:
    FV: float
    NV: float
    SB: float
    GV: float

    def get_total_number(self) -> float:
        return self.FV + self.NV + self.SB + self.GV

    def get_arrival_rate(self, time_frame: int = 60):
        return self.get_total_number() / time_frame
