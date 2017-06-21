from logging import getLogger
from sys import float_info
from threading import Thread, Event

logger = getLogger(__name__)


def get_min_max_county_count(seen_counties):
    minimum = float_info.max
    maximum = float_info.min
    for county, count in seen_counties.items():
        if count < minimum:
            minimum = count

        if count > maximum:
            maximum = count

    return minimum, maximum


def get_seen_counties(tagged_status):
    seen_counties = {}
    for status in tagged_status:
        for county in status.tags["counties"]:
            if county not in seen_counties:
                seen_counties[county] = 1
            else:
                seen_counties[county] += 1
    return seen_counties

def get_uncategorized(tagged_status):
    uncategorized = []
    for status in tagged_status:
        if len(status.tags["counties"]) == 0 and len(status.tags["cities"]) == 0:
            uncategorized.append(status)
    return uncategorized


class ExcThread(Thread):
    def __init__(self, loop_sleep_timeout=0.25):
        self._loop_sleep_timeout = loop_sleep_timeout
        self._stop_event = Event()

        super(ExcThread, self).__init__()

    def stop(self):
        self._stop_event.set()

    def run(self):
        self._do_start()
        while not self._stop_event.isSet():
            self._do_work()
            self._do_wait()
        self._do_stop()

    def _do_start(self):
        pass

    def _do_stop(self):
        pass

    def _do_wait(self):
        self._stop_event.wait(self._loop_sleep_timeout)

    def do_work(self):
        # implement me.
        pass

    def join_with_exception(self):
        # TODO: implement.
        pass


