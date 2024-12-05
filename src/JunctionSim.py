import random

import numpy as np
import pandas
import simpy

from src.RouteSim import RouteSim
from src.SimDataTypes import Train
from typing import Dict, Tuple, List

UPDATE_DELAY = 1. / 600


class JunctionSim:
    def __init__(self,
                 env: simpy.Environment):
        self.env = env
        self.routes: Dict[str, RouteSim] = {}
        self.route_resources: Dict[Tuple[str, str], simpy.Resource] = {}
        self.trains: Dict[int, Train] = {}
        self.last_train_id = 0
        self.resource_queues: Dict[int, Dict[Tuple[str, str], Tuple[List, List]]] = {}

    def add_train(self, route_sim: RouteSim):
        train = Train(self.last_train_id + 1, route_sim.name, self.env.now, None, None, None, False)
        self.last_train_id += 1
        self.trains[train.id] = train
        route_sim.start_train(train)

    def add_route(self, route_sim: RouteSim):
        self.routes[route_sim.name] = route_sim

    def add_resources(self):
        for r1 in self.routes.values():
            for r2 in self.routes.values():
                if (r1.name, r2.name) in self.route_resources.keys():
                    continue
                else:
                    self.route_resources[(r1.name, r2.name)] = simpy.Resource(self.env, 1)
                    # print((r1.name, r2.name), 'added')
                    self.route_resources[(r2.name, r1.name)] = self.route_resources[(r1.name, r2.name)]

    def read_resource_queues(self, minutes_between_read=1):
        while True:
            yield self.env.timeout(minutes_between_read)
            resource_queues = {k: (v.queue, v.users) for k, v in self.route_resources.items()}
            self.resource_queues[self.env.now] = resource_queues

    def log_status(self, until):
        interval = until / 100

        while True:
            yield self.env.timeout(interval)
            now = self.env.now
            print(f'{round(now / until, 2) * 100} % Done')

    def train_scheduler(self):
        while True:
            queues = {k: r.get_queue_length() for k, r in self.routes.items()}
            resources = {k: v.count < 1 for k, v in self.route_resources.items()}
            ready_qs = {k: False for k in self.routes.keys()}
            ready_qs['a-b'] = queues['a-b'] > 0 and resources[('a-b', 'a-b')] and resources[('a-b', 'a-c')]
            ready_qs['a-c'] = queues['a-c'] > 0 and resources[('a-c', 'a-b')] and resources[('a-c', 'a-c')] and \
                              resources[('a-c', 'b-a')]
            ready_qs['b-a'] = queues['b-a'] > 0 and resources[('b-a', 'b-a')] and resources[('b-a', 'c-a')] and \
                              resources[('b-a', 'a-c')]
            ready_qs['c-a'] = queues['c-a'] > 0 and resources[('c-a', 'c-a')] and resources[('c-a', 'b-a')]

            if not any(ready_qs.values()):
                yield self.env.timeout(UPDATE_DELAY)
                continue

            ready_list = [k for k, v in ready_qs.items() if v]
            chosen_key = random.choice(ready_list)

            self.env.process(self.routes[chosen_key].schedule_train())
            yield self.env.timeout(UPDATE_DELAY)

    def run(self, until):
        for k, r in self.routes.items():
            self.env.process(r.spawn_trains())
            self.env.process(r.read_train_length())

        self.env.process(self.train_scheduler())
        self.env.process(self.read_resource_queues())
        self.env.process(self.log_status(until))

    def export_trains(self):
        return {train.id: train for train in self.trains}

    def export_statistics(self, path, start=60, end=1200, additional_data={}, correctness_data={}):
        ql = {k: r.calc_length_of_queue(start=start, end=end) for k, r in self.routes.items()}

        try:
            et_w = {k: r.get_mean_waiting_time(start=start, end=end) for k, r in self.routes.items()}
        except:
            et_w = {k: np.nan for k, r in self.routes.items()}

        data = {r: {'queue_length_query': ql[r],
                    'mean_waiting_time': et_w[r],
                    'arrival_rate': self.routes[r].arrival_rate,
                    'service_rate': self.routes[r].service_rate,
                    'start_at': start,
                    'end_at': end} for r in self.routes.keys()}
        [v.update(additional_data) for v in data.values()]

        if len(correctness_data) > 0:
            [v.update(correctness_data[r]) for r, v in data.items()]

        df = pandas.DataFrame.from_dict(data)

        df.to_csv(path, sep=';', decimal='.')

    def export_statistics_dict(self,start=60, end=1200, additional_data={}, correctness_data={}):
        ql = {k: r.calc_length_of_queue(start=start, end=end) for k, r in self.routes.items()}

        route_data = {r: {'queue_length': ql[r]}
                      for r in self.routes.keys()}
        data = {'start_at': start,
                'end_at': end}

        data.update(additional_data)
        if len(correctness_data) > 0:
            [v.update(correctness_data[r]) for r, v in route_data.items()]

        [data.update({f'{k}_{r}': v2 for k, v2 in v.items()}) for r, v in route_data.items()]

        return data
