from collections import namedtuple

Train = namedtuple('Train', ('id', 'route', 'starting_time', 'ending_time', 'service_start_time', 'service_length' , 'in_service'))