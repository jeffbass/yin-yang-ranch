""" nodehealth: monitor system and network status

    Monitor multiple measures of system and network status, including which
    programs in the yin-yang-ranch system are running. Can be run as a separate
    program from the command line or as part a python program. Intended to be
    run on every computer in the yin-yang-ranch distributed computer vision
    system.

    Copyright (c) 2017 by Jeff Bass.
    License: MIT, see LICENSE for more details.
    """

import logging
import logging.handlers
import signal
import socket
import sys
from tools.utils import clean_shutdown_when_killed
from tools.utils import Settings

def main():
    # set up controlled shutdown when Kill Process or SIGTERM received
    signal.signal(signal.SIGTERM, clean_shutdown_when_killed)

    # load settings for nodehealth abbreviated as nh
    nh = Settings()

    # start logging
    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler(nh.logfile,
        maxBytes=15000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    try:
        log.info('Starting nodehealth.py')
        hostname = socket.gethostname()  # hostname of this computer
        print('This computer is', hostname)
    except (KeyboardInterrupt, SystemExit):
        log.warning('Ctrl-C was pressed or SIGTERM was received.')
    except Exception as ex:
        log.exception('Unanticipated error with no Exception handler.')
    finally:
        log.info('Exited nodehealth.py')
        sys.exit()

if __name__ == '__main__' :
    main()
