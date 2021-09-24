"""gmail_watcher.py: Fetch queries from gmail & sends them to librarian

This program watches Gmail for new messages and sends a selected subset of them
to the libarian via QuerySender ZMQ class. This program is run as a freestanding
main program alonside the librarian program.

Instantiates Gmail which initializes the Gmail service, then loops forever to
watch the Gmail mailbox for any changes. When a change occurs, unread messages
are retrieved. If any of the unread messages are from senders in the contact
list, the text of each of those messages is sent to the libarian as a query.
The Librarian sends a reply back to Gmail from within the librarian program,
not from this program. This program only watches for inbound queries by
monitoring gmail; it does no sending via gmail.

Typically run as a service or background process. See README.rst for details.

Copyright (c) 2020 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import sys
import signal
import traceback
import logging
import logging.handlers
from helpers.library import Settings
from helpers.comms.gmail import Gmail
from helpers.utils import clean_shutdown_when_killed

def main():
    # set up controlled shutdown when Kill Process or SIGTERM received
    signal.signal(signal.SIGTERM, clean_shutdown_when_killed)
    log = start_logging()
    gmail = None  # will allow 'finally:'' to work correctly if no gmail exists
    try:
        log.warning('Starting gmail_watcher.py')
        gmail = None  # will allow finally: to work correctly if no gmail exists
        settings = Settings()  # get settings for communications channels
        details = settings.comm_channels.get('gmail', {})
        gmail = Gmail(settings, details)
        gmail.gmail_watcher(gmail.gmail, gmail.historyId,
                            gmail.mail_check_seconds, gmail.phones_OK_list,
                            gmail.emails_OK_list)
    except (KeyboardInterrupt, SystemExit):
        log.warning('Ctrl-C was pressed or SIGTERM was received.')
    except Exception as ex: # traceback will appear in log
        log.exception('Unanticipated error with no Exception handler.')
    finally:
        if gmail:
            gmail.q_s.close()
        log.info('Exiting gmail_watcher.py')
        sys.exit()

def start_logging():
    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler('gmail_watcher.log',
        maxBytes=95000, backupCount=15)
    formatter = logging.Formatter('%(asctime)s ~ %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.WARNING)
    return log

if __name__ == '__main__' :
    main()
