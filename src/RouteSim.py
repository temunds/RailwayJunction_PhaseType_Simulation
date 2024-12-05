import statistics
import simpy
from src.SimDataTypes import Train
from typing import Dict, Callable

UPDATE_DELAY = 1./600

class RouteSim:
    def __init__(self,
                 env: simpy.Environment,
                 name: str,
                 arrival_generator: Callable[[float], float],
                 service_generator: Callable[[float], float],
                 junction_sim,
                 limited_queue_length: bool = False,
                 limit_queue_length: int = None):
        self.env = env
        self.name = name
        self.arrival_generator = arrival_generator
        self.service_generator = service_generator
        self.junction_sim = junction_sim
        self.trains: Dict[int, Train] = {}
        self.inter_arrival_times = []
        self.service_times_collection = []
        self.lengths: Dict[float, int] = {}
        self.waiting_times: Dict[int, float] = {}
        self.service_times: Dict[int, float] = {}
        self.limited_queue_length: bool = limited_queue_length
        self.limit_queue_length: int = limit_queue_length

    def spawn_trains(self):

        while True:
            inter_arrival = self.arrival_generator(1)
            yield self.env.timeout(inter_arrival)
            self.inter_arrival_times.append(inter_arrival)

            if not self.limited_queue_length:
                self.junction_sim.add_train(self)
            else:
                queue_length = self.get_queue_length()
                if queue_length < self.limit_queue_length:
                    self.junction_sim.add_train(self)

    def schedule_trains(self):
        pass

    def schedule_train(self):
        pass

    def read_train_length(self, minutes_between_read: int = 1):
        while True:
            yield self.env.timeout(minutes_between_read)
            self.lengths[self.env.now] = self.get_queue_length()

    def get_queue_length(self):
        trains_waiting_for_service = [t for t in self.trains.values() if not t.in_service]
        return len(trains_waiting_for_service)

    def run_train(self, train: Train):
        pass

    def finish_train(self, service_start, start_time, train):
        self.trains.pop(train.id)
        train = train._replace(ending_time=self.env.now, in_service=False)
        self.junction_sim.trains[train.id] = train
        end_time = self.env.now
        self.waiting_times[train.id] = service_start - start_time
        self.service_times[train.id] = end_time - service_start

    def start_train(self, train):
        self.trains[train.id] = train

    def calc_length_of_queue(self, start=60, end=120):
        lengths = [v for k, v in self.lengths.items() if k >= start if k <= end]
        return statistics.mean(lengths)

    def get_mean_waiting_time(self, start= 60, end = 120):
        waiting_times = [v for k,v in self.waiting_times.items()
                         if self.get_train(k).service_start_time is not None
                         if self.get_train(k).service_start_time >= start
                         if self.get_train(k).service_start_time <= end]
        return statistics.mean(waiting_times)

    def get_length_after_calculation(self):
        lengths = {k: len([k2 for k2 in self.waiting_times.keys()
                           if self.get_train(k2).starting_time < k
                           if self.get_train(k2).service_start_time >= k
                           if self.get_train(k2).ending_time >= k]) for k in self.lengths.keys()}

        return lengths

    def get_train(self, train_id):
        return self.junction_sim.trains[train_id]

    def get_next_train(self):
        #! uses ordered train numbers by arrival!
        next_train = min(self.trains.keys())
        return self.trains[next_train]

    def service_start_next_train(self):
        train = self.get_next_train()
        service_length = self.service_generator(1)
        self.service_times_collection.append(service_length)
        train = train._replace(in_service=True,
                               service_start_time=self.env.now,
                               service_length=service_length)
        self.trains[train.id] = train
        service_start = self.env.now
        return service_length, service_start, train

    def service_next_train(self):
        service_length, service_start, train = self.service_start_next_train()
        yield self.env.timeout(service_length)
        self.finish_train(service_start, train.starting_time, train)


class RouteSimAB(RouteSim):
    def schedule_trains(self):
        while True:
            if self.get_queue_length() < 1:
                yield self.env.timeout(UPDATE_DELAY)
                continue
            with (self.junction_sim.route_resources[('a-b', 'a-b')].request() as routeAB,
                  self.junction_sim.route_resources[('a-b', 'a-c')].request() as routeAC):
                yield (routeAC & routeAB) | self.env.timeout(UPDATE_DELAY)
                if ((routeAC in self.junction_sim.route_resources[('a-b', 'a-c')].users) and
                    (routeAB in self.junction_sim.route_resources[('a-b', 'a-b')].users)):
                    service_length, service_start, train = self.service_start_next_train()
                    yield self.env.timeout(service_length)
                    self.finish_train(service_start, train.starting_time, train)

    def schedule_train(self):
        with (self.junction_sim.route_resources[('a-b', 'a-b')].request() as routeAB,
              self.junction_sim.route_resources[('a-b', 'a-c')].request() as routeAC):
            yield (routeAC & routeAB)
            service_length, service_start, train = self.service_start_next_train()
            yield self.env.timeout(service_length)
            self.finish_train(service_start, train.starting_time, train)


class RouteSimAC(RouteSim):

    def schedule_trains(self):
        while True:
            if self.get_queue_length() < 1:
                yield self.env.timeout(UPDATE_DELAY)
                continue
            with (self.junction_sim.route_resources[('a-c', 'a-b')].request() as routeAB,
                  self.junction_sim.route_resources[('a-c', 'a-c')].request() as routeAC,
                  self.junction_sim.route_resources[('a-c', 'b-a')].request() as routeBA):
                yield (routeAC & routeAB & routeBA) | self.env.timeout(UPDATE_DELAY)
                if ((routeAB in self.junction_sim.route_resources[('a-c', 'a-b')].users) and
                        (routeAC in self.junction_sim.route_resources[('a-c', 'a-c')].users) and
                        (routeBA in self.junction_sim.route_resources[('a-c', 'b-a')].users)):
                    service_length, service_start, train = self.service_start_next_train()
                    yield self.env.timeout(service_length)
                    self.finish_train(service_start, train.starting_time, train)

    def schedule_train(self):
        with (self.junction_sim.route_resources[('a-c', 'a-b')].request() as routeAB,
              self.junction_sim.route_resources[('a-c', 'a-c')].request() as routeAC,
              self.junction_sim.route_resources[('a-c', 'b-a')].request() as routeBA):
            yield (routeAC & routeAB & routeBA)
            service_length, service_start, train = self.service_start_next_train()
            yield self.env.timeout(service_length)
            self.finish_train(service_start, train.starting_time, train)


class RouteSimBA(RouteSim):

    def schedule_trains(self):
        while True:
            if self.get_queue_length() < 1:
                yield self.env.timeout(UPDATE_DELAY)
                continue
            with (self.junction_sim.route_resources[('b-a', 'c-a')].request() as routeCA,
                  self.junction_sim.route_resources[('b-a', 'a-c')].request() as routeAC,
                  self.junction_sim.route_resources[('b-a', 'b-a')].request() as routeBA):
                yield (routeCA & routeAC & routeBA) | self.env.timeout(UPDATE_DELAY)
                if ((routeCA in self.junction_sim.route_resources[('b-a', 'c-a')].users) and
                    (routeAC in self.junction_sim.route_resources[('b-a', 'a-c')].users) and
                    (routeBA in self.junction_sim.route_resources[('b-a', 'b-a')].users)):
                    service_length, service_start, train = self.service_start_next_train()
                    yield self.env.timeout(service_length)
                    self.finish_train(service_start, train.starting_time, train)

    def schedule_train(self):
        with (self.junction_sim.route_resources[('b-a', 'c-a')].request() as routeCA,
              self.junction_sim.route_resources[('b-a', 'a-c')].request() as routeAC,
              self.junction_sim.route_resources[('b-a', 'b-a')].request() as routeBA):
            yield (routeCA & routeAC & routeBA)
            service_length, service_start, train = self.service_start_next_train()
            yield self.env.timeout(service_length)
            self.finish_train(service_start, train.starting_time, train)


class RouteSimCA(RouteSim):

    def schedule_trains(self):
        while True:
            if self.get_queue_length() < 1:
                yield self.env.timeout(UPDATE_DELAY)
                continue
            with (self.junction_sim.route_resources[('c-a', 'c-a')].request() as routeCA,
                  self.junction_sim.route_resources[('c-a', 'b-a')].request() as routeBA):
                yield (routeCA & routeBA) | self.env.timeout(UPDATE_DELAY)

                if ((routeCA in self.junction_sim.route_resources[('c-a', 'c-a')].users) and
                    (routeBA in self.junction_sim.route_resources[('c-a', 'b-a')].users)):
                    service_length, service_start, train = self.service_start_next_train()
                    yield self.env.timeout(service_length)
                    self.finish_train(service_start, train.starting_time, train)

    def schedule_train(self):
        with (self.junction_sim.route_resources[('c-a', 'c-a')].request() as routeCA,
              self.junction_sim.route_resources[('c-a', 'b-a')].request() as routeBA):
            yield (routeCA & routeBA)
            service_length, service_start, train = self.service_start_next_train()
            yield self.env.timeout(service_length)
            self.finish_train(service_start, train.starting_time, train)


