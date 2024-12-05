import time
import simpy

from src.Simulator import Simulator
from src.JunctionContainer import JunctionContainer, TrainMixContainer
from src.CorrectnessTests import CorrectnessTests

start = time.time()

env = simpy.Environment()

junction = JunctionContainer(TrainMixContainer(6, 0, 0, 0), TrainMixContainer(6, 0, 0, 0), 't', 't2')
junction.time_frame = 60

route_service_rate = {
    'a-b': 0.3,
    'a-c': 0.3,
    'b-a': 0.3,
    'c-a': 0.3
}

setup = time.time()
a = Simulator.run_junction_sim(env, junction, route_service_rate, run_until=1320)
sim = time.time()

print('times:')
print(f'{(setup - start):.4f}s')
print(f'{(sim - setup):.4f}s')
print({k: r.calc_length_of_queue(start=60, end=1260) for k, r in a.routes.items()})

routes = ['a-b', 'a-c', 'b-a', 'c-a']
overlapping_dict = CorrectnessTests.get_no_overlapping_trains(a, routes)

sum_of_conflicts = CorrectnessTests.eval_overlapping_conflicts(a)