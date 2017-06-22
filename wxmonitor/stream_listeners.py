from collections import namedtuple
from logging import getLogger
from threading import RLock

from tweepy import StreamListener

logger = getLogger(__name__)


class ListenerAction(object):
    def __init__(self, *args, **kwargs):
        pass

    def process(self, status):
        pass


class CountingListenerAction(ListenerAction):
    def __init__(self, *args, **kwargs):
        self._counter = 0
        self._lock = RLock()
        super(CountingListenerAction, self).__init__(*args, **kwargs)

    @property
    def counter(self):
        with self._lock:
            return self._counter

    def reset(self):
        with self._lock:
            self._counter = 0

    def process(self, status):
        with self._lock:
            self._counter += 1


class PrintingListenerAction(ListenerAction):
    def process(self, status):
        p = "{0} -- {1} -- {2} -- {3} -- {4}".format(
            status.user.screen_name,
            status.user.location,
            status.coordinates,
            status.lang,
            status.text
        )

        print(p)


ProcessedStatus = namedtuple("ProcessedStatus", field_names=["status", "tags"])


class ProcessingListenerAction(ListenerAction):
    def __init__(self, categorizer, cacher, *args, **kwargs):
        self._categorizer = categorizer
        self._cacher = cacher
        super(ProcessingListenerAction, self).__init__(*args, **kwargs)

    def process(self, status):
        logger.debug("Processing status: %s", status)
        self._cacher.add(ProcessedStatus(status=status, tags=self._categorizer.process(status)))


class TwitterStreamListener(StreamListener):
    def __init__(self, actions_list, *args, **kwargs):
        self._actions_list = actions_list

        super(TwitterStreamListener, self).__init__(*args, **kwargs)

    def on_error(self, status_code):
        logger.warning("Error encountered %d", status_code)
        if status_code == 420:
            logger.error("Error is 420, that is a rate limit. shutting down connection.")
            return False

    def on_status(self, status):
        for action in self._actions_list:
            action.process(status)

    def on_limit(self, track):
        logger.warning("Limits exceeded")
