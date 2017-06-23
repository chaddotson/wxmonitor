from argparse import ArgumentParser
from configparser import RawConfigParser
from logging import DEBUG, getLogger, INFO, basicConfig

from tweepy import API, OAuthHandler, Stream

from wxmonitor.cache import Cache
from wxmonitor.reporting import ProcessingImpl, ProcessingWorkerThread, TweetReportOutput
from wxmonitor.stream_listeners import LoggingStreamListenerAction, PrintingListenerAction, ProcessingListenerAction,\
    TwitterStreamListener
from wxmonitor.weather_categorizer import WeatherCategorizer

logger = getLogger(__name__)


def parse_args():
    parser = ArgumentParser(description='Weather monitor')
    parser.add_argument('tracking_tag', help='Tracking tag', type=str)
    parser.add_argument('bot_name', help='Bot screen name', type=str)
    parser.add_argument('places', help='Places File', type=str)
    parser.add_argument('-t', '--twitter', help='Twitter configuration (arg = twitter.cfg)', type=str, default="./twitter.cfg")

    parser.add_argument('-l', '--log', help='Log tweet contents', default=None)
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

    logging_action = None
    printer_action = PrintingListenerAction()
    processing_action = ProcessingListenerAction(categorizer, cache)

    actions = [printer_action, processing_action]

    if args.log:
        logging_action = LoggingStreamListenerAction(args.log)
        logging_action.start_logger()
        actions.append(logging_action)

    tweet_report_generator = TweetReportOutput(tweet_api=api)

    processing_impl = ProcessingImpl(reporter=tweet_report_generator, cacher=cache, tracking_tag=args.tracking_tag)
    processing_thread = ProcessingWorkerThread(processor_impl=processing_impl)
    processing_thread.start()

    listener = TwitterStreamListener(bot_screen_name=args.bot_name,  actions_list=actions)
    stream = Stream(auth=api.auth,
                    listener=listener)

    logger.info("\nBot Name: %s\nTracking: %s", args.bot_name, args.tracking_tag)

    try:
        stream.filter(track=[args.tracking_tag], async=False)

    except KeyboardInterrupt:
        pass

    except:
        logger.exception('Unknown failure')

    processing_thread.stop()
    stream.disconnect()

    if logging_action:
        logging_action.stop_logger()


def configure_twitter_api(twitter_configuration_file):
    config = RawConfigParser()
    config.read(twitter_configuration_file)
    auth = OAuthHandler(config.get('TWITTER', 'CONSUMER_KEY'),
                        config.get('TWITTER', 'CONSUMER_SECRET'))
    auth.set_access_token(config.get('TWITTER', 'ACCESS_KEY'),
                          config.get('TWITTER', 'ACCESS_SECRET'))
    api = API(auth)
    return api


if __name__ == '__main__':
    main()

