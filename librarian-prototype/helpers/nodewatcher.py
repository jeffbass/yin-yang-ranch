"""imagenode_watcher: monitor imagenodes using command 'systemctl status'

Some errors on Raspberry Pi's running imagenode cameras and temperature sensors
send error messages to the systemctl / journalctl logs, but fail to exit and
restart the program. They hang in modules that are written in C and give an
error message to the systemctl / journalctl logs, but then stall / freeze. It
takes a "sudo systemctl restart imagenode" to restart them. The purpose of this
module is to run "systemctl status imagenode", recognize those errors and then
run "sudo systemctl restart imagenode" to restart the imagenode.

This is an experimental module to try better ways of finding and fixing these
imagenode stalls. Prior to restarting, the error messages are written to the
log file. As these logs are gathered, it is hoped that a pattern will emerge so
a more elegant and specific code fix can be implemented.

Packages that are repeat offenders in these hangs / stalls are: 1) PiCamera
module, 2) DHT-22 Adafruit_blinka module and 3) ZMQ. The errors are rare and
may just be due to power glitches. This module tracks them, logs the error and
then restarts imagenode.

Copyright (c) 2020 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import os
import sys
import signal
import logging
import traceback
import subprocess
import multiprocessing
import logging.handlers
from time import sleep
from helpers.utils import clean_shutdown_when_killed

class SystemctlMonitor:
    """ Use Linux systemctl command to monitor imagenode system stability

    ASSUMES that imagenode was started with "sudo systemctl restart imagenode".
    This means that there is an imagenode.service file defined and that it
    is setup to appropriately start, restart, stop and check status of
    imagenode.py. And that the user running the command has sudo priveleges.

    If imagenode.py was started by any other means, this Class will not be able
    to successfully restart it.

    To use this class in a free standing "main" program:
        python imagenode_watcher.py  # assumes librarian Settings is set up

    To use in another program as a multiprocessing.Process:
        sm = SystemctlMonitor(log)  # log is the logger instance
        patience = settings.patience  # assumes settings is set up elsewhere
        imagenodes = settings.imagenode  # ditto
        systemctl_p = None
        if settings.systemctl_watcher:  # systemctl_watcher option set to True
            systemctl_p = multiprocessing.Process(daemon=True,
                          args=((patience, imagenodes,)),
                          target=sm.systemctl_watcher)
            systemctl_p.start()

    To use in another program as a threading.Thread, use the code above and
    change "multiprocessing.Process" to "threading.Thread"

    """
    def __init__(self, log):
        self.status_cmd = 'systemctl status imagenode'  # preferred approach
        self.journal_cmd = 'journalctl -u imagenode'  # an alternative approach
        self.restart_cmd = 'sudo systemctl restart imagenode'
        self.log = log

    def systemctl_watcher(self, patience, imagenodes):
        """ Watch the imagenodes using "systemctl status imagenode"

        This method is started in a separate thread or process. It sleeps for
        'patience' seconds, then checks each imagenode in the imagenodes list.
        Then repeats forever.

        For each imagenode:
        It runs the command "systemctl status imagenode", then
        checkes that the last line of the returned contains
        "Started Imagenode Service". If not, it restarts the imagenode using the
        command "sudo systemctl restart imagenode".

        This requires that each imagenode computer be setup up so that it has
        passwordless login from the computer that is running this program.
        It also assumes that the login user speciried in the imagenode list
        (often "pi") has sudo priveleges. If passwordless login fails, then
        this program will fail without warning (TODO: fix this).

        The list of imagenodes looks like:
            imagenodes = ['pi@rpi11', 'pi@rpi12', 'pi@rpi14', 'pi@rpi19']

        Parameters:
            patience (int): how long to wait for each check
            imagenodes (list): the list of imagenodes to check
        """
        while True:
            sleep(patience)
            for imagenode in imagenodes:
                if not self.imagenode_OK(imagenode):
                    self.restart_imagenode(imagenode)

    def imagenode_OK(self, imagenode):
        """ check the imagenode is OK using systemctl status command.
        """
        # use ssh to run the systemctl status command
        # TODO: add a timeout for case where ssh does not successfully log in
        #       for example, if the imagenode computer is not running.
        status = subprocess.run(['ssh', imagenode, self.status_cmd],
                capture_output=True, text=True)
        lines = status.stdout.splitlines()
        if lines:  # were any lines returned?
            if 'started imagenode service' in lines[-1].lower():
                # last line of systemctl status contains above phrase then OK
                return True
            # elif (some_test_on.conditions):  #############  Need tests for Error, Exception,

            # see this note in Evernote: Various imagenode error and exception notes -- List Note
            # TODO: add a test for a Journal rotation line like:
            # Warning: Journal has been rotated since unit was started.
            # systemctl status  response lines like that should return True?
            self.log.error("**imagenode error " + imagenode +
                            ". Last lines from systemctl status:")
            for line in lines[-5:]:
                self.log.error('  ' + line)
            return False
        else:  # no lines were returned; imagenode not OK
            return False

    def restart_imagenode(self, imagenode):
        """ restart the imagenode using systemctl restart
        """
        status = subprocess.run(['ssh', imagenode, self.restart_cmd],
                capture_output=True, text=True)
        self.log.error("restarted imagenode " + imagenode)
        return self.imagenode_OK(imagenode)  # check imagenode status again

def start_logging():
    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler('imagenode_watcher.log',
        maxBytes=95000, backupCount=15)
    formatter = logging.Formatter('%(asctime)s ~ %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.WARNING)
    return log

def main():
    # set up controlled shutdown when Kill Process or SIGTERM received
    signal.signal(signal.SIGTERM, clean_shutdown_when_killed)
    log = start_logging()
    try:
        log.warning('Starting imagenode_watcher.py')
        # TODO: modify Settings class to include imagenodes list
        # settings = Settings()  # get settings: patience & imagenodes list
        sm = SystemctlMonitor(log)
        patience = 30  # how often to check the imaagenodes in seconds
        # imagenodes list for testing; will get from Settings() later
        imagenodes = ['pi@rpi11', 'pi@rpi12', 'pi@rpi14', 'pi@rpi19',
                        'pi@rpi20']
        sm.systemctl_watcher(patience, imagenodes)
    except (KeyboardInterrupt, SystemExit):
        log.warning('Ctrl-C was pressed or SIGTERM was received.')
    except Exception as ex: # traceback will appear in log
        log.exception('Unanticipated error with no Exception handler.')
    finally:
        log.info('Exiting imagenode_watcher.py')
        sys.exit()

if __name__ == '__main__' :
    main()
