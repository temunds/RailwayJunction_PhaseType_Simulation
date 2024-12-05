
import simpy
from src.JunctionContainer import JunctionContainer
from src.JunctionSim import JunctionSim
from src.RouteSim import RouteSimAB, RouteSimAC, RouteSimBA, RouteSimCA
from src.StatisticHelper import StatisticHelper
from typing import Dict


class Simulator:

    @staticmethod
    def run_junction_sim(env: simpy.Environment,
                         junction: JunctionContainer,
                         route_service_rate: Dict[str, float],
                         run_until: float = 120):

        junction_sim = Simulator.create_junction_sim_ph(env, junction, route_service_rate)

        junction_sim.run(run_until)
        env.run(until=run_until)

        return junction_sim


    @staticmethod
    def create_junction_sim_ph(env, junction, route_service_rate):
        junction_sim = JunctionSim(env)
        route_ab = RouteSimAB(env,
                              'a-b',
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  junction.main_branch_mix.get_arrival_rate(junction.time_frame),
                                  0.8),
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  route_service_rate['a-b'],
                                  0.3),
                              junction_sim)
        route_ac = RouteSimAC(env,
                              'a-c',
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  junction.side_branch_mix.get_arrival_rate(junction.time_frame),
                                  0.8),
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  route_service_rate['a-c'],
                                  0.3),
                              junction_sim)
        route_ba = RouteSimBA(env,
                              'b-a',
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  junction.main_branch_mix.get_arrival_rate(junction.time_frame),
                                  0.8),
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  route_service_rate['b-a'],
                                  0.3),
                              junction_sim)
        route_ca = RouteSimCA(env,
                              'c-a',
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  junction.side_branch_mix.get_arrival_rate(junction.time_frame),
                                  0.8),
                              StatisticHelper.get_ph_generator_from_rate_and_cov(
                                  route_service_rate['c-a'],
                                  0.3),
                              junction_sim)
        junction_sim.add_route(route_ab)
        junction_sim.add_route(route_ac)
        junction_sim.add_route(route_ba)
        junction_sim.add_route(route_ca)

        junction_sim.add_resources()

        return junction_sim