"""utils: various utility functions used by imagenode and imagehub

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import sys
import time
import signal
import logging
import multiprocessing

def clean_shutdown_when_killed(signum, *args):
    """Close all connections cleanly and log shutdown
    This function will be called when SIGTERM is received from OS
    or if the program is killed by "kill" command. It then raises
    KeyboardInterrupt to close all resources and log the shutdown.
    """
    logging.warning('SIGTERM detected, shutting down')
    sys.exit()

def interval_timer(interval, action):
    """ Call the function 'action' every 'interval' seconds

    This is typically used in a thread, since it blocks while it is sleeping
    between action calls. For example, when a check_temperature sensor is
    instantiated, this timer is started in a thread to call the
    check_temperature function at specified intervals.

    Parameters:
        interval (int): How often to call the function 'action' in seconds
        action (function): Function to call
    """
    next_time = time.time() + interval
    while True:
        time.sleep(max(0, next_time - time.time()))
        try:
            action()
        except (KeyboardInterrupt, SystemExit):
            logging.warning('Ctrl-C was pressed or SIGTERM was received.')
            raise
        except Exception:
            logging.exception('Error in interval_timer')
        next_time += (time.time() - next_time) // interval * interval + interval

class YamlOptionsError(Exception):
    pass

class Patience:
    """Timing class using system ALARM signal.

    When instantiated, starts a timer using the system SIGALRM signal. To be
    used in a with clause to allow a blocking task to be interrupted if it
    does not return in specified number of seconds.

    See main event loop in Imagenode.py for Usage Example

    Parameters:
        seconds (int): number of seconds to wait before raising exception
    """
    class Timeout(Exception):
        pass

    def __init__(self, seconds):
        self.seconds = seconds

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.raise_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, *args):
        signal.alarm(0)    # disable alarm

    def raise_timeout(self, *args):
        raise Patience.Timeout()

class StallWatcher:
    def __init__(self):
        self.stall_p = None
        if settings.stall_watcher:  # stall_watcher option set to True
            pid = os.getpid()
            self.stall_p = multiprocessing.Process(daemon=True,
                               args=((pid, self.patience,)),
                               target=self.stall_watcher)
            self.stall_p.start()

    def stall_watcher(self, pid, patience):
        """ Watch the main process cpu_times.user; sys.exit() if not advancing

        Parameters:
            pid (int): process ID of the main imagenode process
            patience (int): how long to wait for each check repeated check
        """
        p = psutil.Process(pid)
        main_time = p.cpu_times().user
        sleep_time = patience
        sleep(sleep_time)
        while True:
            last_main_time = main_time
            main_time = p.cpu_times().user
            delta_time = round(abs(main_time - last_main_time))
            if delta_time < 1:
                os.kill(pid, signal.SIGTERM) # p.terminate() # or os.kill(pid, signal.SIGTERM)
                sys.exit()
            sleep(sleep_time)
