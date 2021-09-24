"""CLI_chat_echo_test - provide test echo for ZMQ test of CLI_chat.py

This program acts as a super simple Librarian to test CLI_chat.py. It assumes
that it is receiving a simple message composed of only of text via ZMQ. It
assumes that the text came from a terminal window CLI. It assumes that there is
only one CLI source and makes no attempt to identify a specific user name.

This program is run from the command line (CLI) to provide an echo of text
sent by the CLI_chat.py program. It provides the same imagezmq.ImageHub() that
the Librarian.py provides so that the CLI_chat.py program can be tested.

First, edit the tcp address and port in this program.
Then, edit the tcp address and port in the CLI_chat.py program.
Then, in one terminal window, run this program:
    python CLI_chat_echo_test.py
Finally, in another terminal window, run the CLI_chat.py program:
    python CLI_chat.py

Copyright (c) 2020 by Jeff Bass.
License: MIT, see LICENSE for more details.

"""

import sys
import imagezmq
import traceback
from time import sleep
from imagezmq import ImageHub

# open imageZMQ hub to simulate Librarian
# use any of the formats below to specifiy address of display computer
# librarian = imagezmq.ImageHub(open_port='tcp://:5555')
# librarian = imagezmq.ImageHub()

class QueryReceiver(ImageHub):
    def __init__(self, open_port='tcp://*:5555', REQ_REP = True):
        ImageHub.__init__(self, open_port=open_port, REQ_REP = REQ_REP)
    def receive_query(self):
        query, buf = self.recv_jpg()  # send_jpg returns a bytestring
        # query = query_b.decode('utf-8') # decode from bytes to Python 3 string
        return query

def main():
    librarian = QueryReceiver()
    receive_query = librarian.receive_query  # rename imagezmq functions
    send_reply = librarian.send_reply

    try:
        while True:
            query = receive_query()
            reply = 'What you said was: ' + query  # compose a simple echo reply
            reply = reply.encode()  # convert string to bytes to make ZMQ happy
            send_reply(reply)
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
    except Exception as ex:
        traceback.print_exc()
    finally:
        librarian.close()
        sys.exit()

if __name__ == '__main__' :
    main()
