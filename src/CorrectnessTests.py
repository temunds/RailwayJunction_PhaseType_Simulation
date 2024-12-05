from src.JunctionSim import JunctionSim

from typing import List


class CorrectnessTests:

    @staticmethod
    def get_overlapping_trains(junction_sim: JunctionSim, route1: str, route2: str):
        trains_overlapping = [(k1, k2) for k1, t1 in junction_sim.trains.items() for k2, t2 in
                              junction_sim.trains.items()
                              if t1.ending_time is not None if t2.ending_time is not None
                              if max(t1.service_start_time, t2.service_start_time) < min(t1.ending_time, t2.ending_time)
                              if t1.route == route1 if t2.route == route2]

        return trains_overlapping

    @staticmethod
    def get_no_overlapping_trains(junction_sim: JunctionSim, routes: List[str]):
        overlapping_dict = {(r1, r2): len(CorrectnessTests.get_overlapping_trains(junction_sim, r1, r2))
                            for r1 in routes
                            for r2 in [r for r in routes if r != r1]}
        return overlapping_dict

    @staticmethod
    def eval_overlapping_conflicts(junction_sim: JunctionSim):
        routes = ['a-b', 'a-c', 'b-a', 'c-a']
        overlapping_dict = CorrectnessTests.get_no_overlapping_trains(junction_sim, routes)

        conflicting_routes = [('a-b', 'a-c'), ('a-c', 'a-b'), ('a-c', 'b-a'), ('b-a', 'a-c'), ('b-a', 'c-a'),
                              ('c-a', 'b-a')]

        sum_of_conflicts = sum(overlapping_dict[c] for c in conflicting_routes)

        return sum_of_conflicts