from src.TrainMixContainer import TrainMixContainer
from dataclasses import dataclass


@dataclass
class JunctionContainer:
    main_branch_mix: TrainMixContainer
    side_branch_mix: TrainMixContainer
    main_line_name: str
    branch_line_name: str
    time_frame: int = None

    def get_arrival_rate_main_branch(self):
        return self.main_branch_mix.get_arrival_rate()

    def get_arrival_rate_side_branch(self):
        return self.side_branch_mix.get_arrival_rate()

    def get_total_number_of_trains(self):
        return self.side_branch_mix.get_total_number() + self.main_branch_mix.get_total_number()
