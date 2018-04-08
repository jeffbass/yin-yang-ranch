"""utils: various utility functions used by imagenode

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import logging
import signal

log = logging.getLogger(__name__)

def clean_shutdown_when_killed(signum, *args):
    ''' This will close all connections cleanly
        and make sure the Kill or SIGTERM is logged
        and will make sure the finally clause is executed
    '''
    logging.warning("SIGTERM detected, shutting down")
    raise KeyboardInterrupt # this works well from inside the main forever loop

class Timeout():
    """Timeout class using ALARM signal."""
    class Timeout(Exception):
        pass

    def __init__(self, sec):
        self.sec = sec

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.sec)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Timeout.Timeout()

class Settings():
    """Load settings. During testing using assignment; later using YAML file"""
    def __init__(self):
        self.logfile = 'logs/nodehealth.log'
