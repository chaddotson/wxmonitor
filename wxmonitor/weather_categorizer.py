import re
from csv import DictReader
from logging import getLogger

logger = getLogger(__name__)


class WeatherCategorizer(object):
    _events_regex_str = r"(\bnnow\b|\brain\b|\bhail\b|\btrees.*?down\b|\bdamage\b|\broof\b|\bponding\b|\bflooding\b|\bflood\b|\bwind\b)"

    def __init__(self, ansi_code_file):
        # get ansi code file from: https://www.census.gov/geo/reference/codes/place.html

        self._cities = set()
        self._counties = set()
        self._zipcodes = set()

        self._city_county_map = {}
        self._city_zip_map = {}

        self._city_location_regex = None
        self._county_location_regex = None
        self._event_type_regex = None

        self._ansi_code_file = ansi_code_file
        self._build_place_data()
        self._build_regexes()

    def _build_place_data(self):

        logger.debug("Building place data with ansi code file: %s", self._ansi_code_file)
        with open(self._ansi_code_file, "r") as f:
            reader = DictReader(f, delimiter="|")

            for row in reader:
                zipcode = row["PLACEFP"]
                city = " ".join(row["PLACENAME"].split()[:-1]).lower()

                for county in map(str.strip, row["COUNTY"].split(",")):
                    county = county.lower()

                    self._counties.add(county.lower())

                    if self._city_county_map.get(city) is None:
                        self._city_county_map[city] = []

                    self._city_county_map[city].append(county)

                self._zipcodes.add(zipcode)
                self._cities.add(city)
                self._city_zip_map[city] = zipcode
                self._city_zip_map[zipcode] = city
        logger.debug("Done")

    def _build_regexes(self):
        logger.debug("Building regexes")
        cities_regex_str = "(" + r"\b|\b".join(self._cities) + ")+"
        counties_regex_str = "(" + r"\b|\b".join(self._counties) + ")+"
        events_regex_str = self._events_regex_str
        spotter_retex_str = "#tspotter"

        self._city_location_regex = re.compile(cities_regex_str, re.IGNORECASE | re.MULTILINE)
        self._county_location_regex = re.compile(counties_regex_str, re.IGNORECASE | re.MULTILINE)
        self._event_type_regex = re.compile(events_regex_str, re.IGNORECASE | re.MULTILINE)
        self._spotter_regex = re.compile(spotter_retex_str, re.IGNORECASE | re.MULTILINE)
        logger.debug("Done")

    def process(self, status):
        logger.debug("Processing: %s", status)

        content = status.text

        cities = list(set(city.lower() for city in self._city_location_regex.findall(content)))
        counties = self._county_location_regex.findall(content)

        for city in cities:
            if city in self._city_county_map and self._city_county_map[city] is not None:
                counties.extend(self._city_county_map[city])

        counties = list(set(" ".join(county.split()[:-1]).lower() for county in counties))
        events = list(set(map(str.lower, self._event_type_regex.findall(content))))

        logger.debug("Done\n - Cities: %s\n - Counties: %s\n - Events: %s", cities, counties, events)

        return {
            "cities": cities,
            "counties": counties,
            "events": events,
            "spotter": self._spotter_regex.search(content) is not None
        }
