from argparse import ArgumentParser
from configparser import RawConfigParser
from logging import DEBUG, getLogger, INFO, basicConfig

from tweepy import API, OAuthHandler, Stream

from wxmonitor.cache import Cache
from wxmonitor.reporting import ProcessingImpl, ProcessingWorkerThread, TweetReportOutput
from wxmonitor.stream_listeners import PrintingListenerAction, ProcessingListenerAction, TwitterStreamListener
from wxmonitor.weather_categorizer import WeatherCategorizer

logger = getLogger(__name__)


def parse_args():
    parser = ArgumentParser(description='Weather monitor')
    parser.add_argument('places', help='Places File', type=str)
    parser.add_argument('-t', '--twitter', help='Twitter configuration (arg = twitter.cfg)', type=str, default="./twitter.cfg")

    parser.add_argument('-l', '--log', help='Log categorizations', default=False, action='store_true')
    parser.add_argument('-v', '--verbose', help='Verbose logs', default=False, action='store_true')

    return parser.parse_args()


def main():
    logging_config = dict(level=INFO,
                          format='[%(asctime)s - %(filename)s:%(lineno)d - %(funcName)s - %(levelname)s] %(message)s')
    basicConfig(**logging_config)

    args = parse_args()

    if args.verbose:
        getLogger('').setLevel(DEBUG)

    api = configure_twitter_api(args.twitter)

    categorizer = WeatherCategorizer(args.places)
    cache = Cache()
    printer_action = PrintingListenerAction()
    processing_action = ProcessingListenerAction(categorizer, cache)

    tweet_report_generator = TweetReportOutput(tweet_api=api)

    processing_impl = ProcessingImpl(reporter=tweet_report_generator, cacher=cache)
    processing_thread = ProcessingWorkerThread(processor_impl=processing_impl)
    processing_thread.start()

    listener = TwitterStreamListener(actions_list=[printer_action, processing_action])
    stream = Stream(auth=api.auth,
                    listener=listener)

    try:
        stream.filter(track=['#tnwx'], async=False)

    except KeyboardInterrupt:
        pass

    except:
        logger.exception("Unknown failure")

    processing_thread.stop()
    stream.disconnect()


def configure_twitter_api(twitter_configuration_file):
    config = RawConfigParser()
    config.read(twitter_configuration_file)
    auth = OAuthHandler(config.get("TWITTER", "CONSUMER_KEY"),
                        config.get("TWITTER", "CONSUMER_SECRET"))
    auth.set_access_token(config.get("TWITTER", "ACCESS_KEY"),
                          config.get("TWITTER", "ACCESS_SECRET"))
    api = API(auth)
    return api


if __name__ == "__main__":
    main()

