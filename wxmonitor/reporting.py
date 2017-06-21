from io import BytesIO
from logging import getLogger
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from tempfile import NamedTemporaryFile
from time import time

from wxmonitor.graphing import make_basemap, make_county_hash, get_rgb
from wxmonitor.utils import ExcThread, get_seen_counties, get_min_max_county_count, get_uncategorized

logger = getLogger(__name__)


class ReportingWorkerThread(ExcThread):

    def __init__(self, cacher, seconds_between_reports=600):
        self._impl = ReporterImpl(cacher, seconds_between_reports)
        super(ReportingWorkerThread, self).__init__(loop_sleep_timeout=120)

    def _do_work(self):
        self._impl.process()

    def _do_start(self):
        logger.debug("Starting reporter worker.")

    def _do_stop(self):
        logger.debug("Stopping reporter worker.")


class ReporterImpl(object):
    def __init__(self, twitter_api, cacher, seconds_between_reports, image_format="png"):
        self._twitter_api = twitter_api
        self._prev_cacher_len = 0
        self._cacher = cacher
        self._seconds_between_reports = seconds_between_reports
        self._image_format = image_format

        self._next_report_time_threshold = None
        self._set_next_report_time_threshold()

    def _report_time_threshold_exceeded(self):
        return time() >= self._next_report_time_threshold

    def _set_next_report_time_threshold(self):
        self._next_report_time_threshold = time() * self._seconds_between_reports

    def process(self):
        statuses = self._cacher.get_statuses()

        current_len = len(statuses)

        print("Checking")

        if not ((self._prev_cacher_len == 0 and current_len > 0) or
                    (self._prev_cacher_len > 0 and current_len == 0) or
                    (current_len != 0 and self._report_time_threshold_exceeded())):
            return

        print("processing!")

        seen_counties = get_seen_counties(statuses)
        minimum, maximum = get_min_max_county_count(seen_counties)
        uncategorized = get_uncategorized(statuses)

        print(seen_counties)

        print("There are {0} uncategorized tweets.".format(len(uncategorized)), uncategorized)

        image_bytes = self.make_image(maximum, minimum, seen_counties)


        # with NamedTemporaryFile(suffix=".png") as f:
        #     f.write(image_bytes.read())
        #     self._twitter_api.update_with_media(f.name, "this is a test... beep beep beep")

        self._set_next_report_time_threshold()

    def make_image(self, maximum, minimum, seen_counties):
        plt.figure(figsize=(12, 6))
        # TODO: make this configurable... TN for now.
        state_map = make_basemap(lat_0=39.1622, lon_0=-86.5292,
                                 lower_left_lon=-90.60, lower_left_lat=34.80,
                                 upper_right_lon=-81.31, upper_right_lat=36.71)
        ax = plt.gca()
        for county, count in seen_counties.items():
            seg = state_map.county_poly_map[make_county_hash("tn", county)]
            poly = Polygon(seg, facecolor=get_rgb(count, minimum, maximum), edgecolor=(0.9, 0.9, 0.9))
            ax.add_patch(poly)

        plt.show()

        results = BytesIO()
        plt.savefig(results, format=self._image_format)
        results.seek(0)

        return results


