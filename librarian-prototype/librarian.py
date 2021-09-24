"""librarian: answer questions using imagehub event messages, images sensor data

Answers questions about currrent and past observations of imagenodes, including
inputs from PiCameras, USB Webcams, temperature sensors, etc.

Gathers image, sensor and event logs from imagehubs. Does analysis such as
object detection and classification on images. Monitors operational status of
imagenodes and imagehubs. Manages multiple modes of communications for queries
and alerts.

Typically run as a service or background process. See README.rst for details.

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import sys
import signal
import logging
import logging.handlers
import time
import traceback
from helpers.library import Settings
from helpers.library import Librarian
from helpers.utils import clean_shutdown_when_killed

def main():
    # set up controlled shutdown when Kill Process or SIGTERM received
    signal.signal(signal.SIGTERM, clean_shutdown_when_killed)
    log = start_logging()
    try:
        log.warning('Starting librarian.py')
        settings = Settings()  # get settings for hubs, communications channels
        librarian = Librarian(settings)  # start all the librarian processes
        # forever event loop
        while True:
            # for each initialized librarian communications channel
            for channel in librarian.comm_channels:
                # Listen for and respond to incoming questions
                request = channel.next_query()
                if request:
                    reply = librarian.compose_reply(request)
                    channel.send_reply(reply)
                time.sleep(1)  # sleep before next channel check

    except (KeyboardInterrupt, SystemExit):
        log.warning('Ctrl-C was pressed or SIGTERM was received.')
    except Exception as ex:  # traceback will appear in log
        log.exception('Unanticipated error with no Exception handler.')
    finally:
        if 'librarian' in locals():
            librarian.closeall(settings) # close files and communications
        log.info('Exiting librarian.py')
        sys.exit()

def start_logging():
    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler('librarian.log',
        maxBytes=95000, backupCount=15)
    formatter = logging.Formatter('%(asctime)s ~ %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.WARNING)
    return log

if __name__ == '__main__' :
    main()
