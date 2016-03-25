import logging

logging.basicConfig(
    format='[%(asctime)s] [%(process)d] [%(name)s] [%(levelname)s] '
           '%(message)s',
    datefmt='%Y-%m-%d %H:%M:%S +0000', level=logging.DEBUG)
LOG = logging.getLogger(__name__)


def logger():
    return LOG
