"""utils: various utility functions used by imagenode and imagehub

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""
import signal
import logging

def clean_shutdown_when_killed(signum, *args):
    """Close all connections cleanly and log shutdown
    This function will be called when SIGTERM is received from OS
    or if the program is killed by "kill" command. It then raises
    KeyboardInterrupt to close all resources and log the shutdown.
    """
    logging.warning("SIGTERM detected, shutting down")
    raise KeyboardInterrupt

class Patience:
    """Timing class using system ALARM signal.
    See main event loop in Imagenode.py for Usage Example
    """
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
        raise Patience.Timeout()
