from io import BytesIO
from logging import getLogger
import matplotlib as mpl
mpl.use('Agg')
from matplotlib import pyplot as plt
from matplotlib.patches import Polygon
from tempfile import NamedTemporaryFile
from datetime import datetime, timedelta

from wxmonitor.graphing import make_basemap, make_county_hash, get_rgb
from wxmonitor.utils import ExcThread, get_seen_counties, get_min_max_county_count, get_uncategorized

logger = getLogger(__name__)


class ProcessingWorkerThread(ExcThread):
    def __init__(self, processor_impl):
        logger.debug("Start data processing worker.")
        self._impl = processor_impl
        super(ProcessingWorkerThread, self).__init__(loop_sleep_timeout=120)

    def _do_work(self):
        logger.debug("Processing...")
        self._impl.process()
        logger.debug("Processing Complete")

    def _do_start(self):
        logger.debug("Starting reporter worker.")

    def _do_stop(self):
        logger.debug("Stopping reporter worker.")


class ProcessingImpl(object):
    def __init__(self, reporter, cacher, tracking_tag, seconds_between_reports=300, image_format="png"):
        logger.debug("Creating Processing Impl.")
        self._reporter = reporter
        self._cacher = cacher
        self._tracking_tag = tracking_tag
        self._prev_cacher_len = 0
        self._seconds_between_reports = seconds_between_reports
        self._image_format = image_format

        self._next_report_time_threshold = None
        self._set_next_report_time_threshold()

    def _report_time_threshold_exceeded(self):
        return datetime.now() >= self._next_report_time_threshold

    def _set_next_report_time_threshold(self):
        self._next_report_time_threshold = datetime.now() + timedelta(seconds=self._seconds_between_reports)
        logger.debug("Next report time: %s", self._next_report_time_threshold)

    def process(self):
        statuses = self._cacher.get_statuses()

        current_len = len(statuses)


        logger.debug("(self._prev_cacher_len == 0 and current_len > 0) => %s",
                     (self._prev_cacher_len == 0 and current_len > 0))

        logger.debug("(self._prev_cacher_len > 0 and current_len == 0) => %s",
                     (self._prev_cacher_len > 0 and current_len == 0))

        logger.debug("(current_len != 0 and not self._report_time_threshold_exceeded()) => %s",
                     (current_len != 0 and self._report_time_threshold_exceeded()))

        if not ((self._prev_cacher_len == 0 and current_len > 0) or
                    (self._prev_cacher_len > 0 and current_len == 0) or
                    (current_len != 0 and self._report_time_threshold_exceeded())):
            return

        self._prev_cacher_len = current_len

        logger.debug("Cache len changed from/to Zero or the report threshold has been exceeded.")

        seen_counties = get_seen_counties(statuses)
        minimum, maximum = get_min_max_county_count(seen_counties)
        uncategorized = get_uncategorized(statuses)

        logger.debug("Seen counties: %s", repr(seen_counties))

        logger.debug("Uncategorized Statuses: %d", len(uncategorized))

        #print("There are {0} uncategorized tweets.".format(len(uncategorized)), uncategorized)

        self.render_map(maximum, minimum, seen_counties)

        summary = "Data over 1hr\nTotal Statuses: {0}\nTotal Uncategorized: {1}\n{2}".format(current_len,
                                                                                             len(uncategorized),
                                                                                             self._tracking_tag)

        self._reporter.create_output(summary=summary)

        self._set_next_report_time_threshold()

    def render_map(self, maximum, minimum, seen_counties):
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


class ReportOutput(object):
    def create_output(self, **data):
        return None


class DisplayReportOutput(ReportOutput):
    def create_output(self, **data):
        print("Summary:" + data.get("summary", "")[0:140])
        plt.show()
        return None


class FileReportOutput(ReportOutput):
    def __init__(self, filename, format="png", reset_seek=True):
        self._filename = filename
        self._format = format
        self._reset_seek = reset_seek

    def create_output(self, **data):
        plt.savefig(self._filename, format=self._format)
        return self._filename


class BytesReportOutput(ReportOutput):
    def __init__(self, format="png", reset_seek=True):
        self._format = format
        self._reset_seek = reset_seek

    def create_output(self, **data):
        results = BytesIO()
        plt.savefig(results, format=self._format)

        if self._reset_seek:
            results.seek(0)

        return results


class TweetReportOutput(BytesReportOutput):
    def __init__(self, tweet_api):
        logger.debug("Creating tweet report generator")
        self._api = tweet_api

        super(TweetReportOutput, self).__init__(format="png")

    def create_output(self, **data):
        output = super(TweetReportOutput, self).create_output(**data)

        with NamedTemporaryFile(suffix=".png") as f:
            f.write(output.read())
            logger.debug("Named Temp File: %s", f.name)
            self._api.update_with_media(f.name, data.get("summary", "")[0:140])

        return output




