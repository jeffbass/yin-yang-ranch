"""CLI_chat - Program started by user to chat with Librarian via CLI

This program is run from the command line (CLI) to allow the user to start
a conversation. It can be run on the same computer as the librarian or on a
different computer as long as a tcp address (and, optionally a port) are
specified.

This program demonstrates the QuerySend class which inheirits from
imageZMQ ImageSender class. The QuerySender class uses the ImageSender
send_jpg method and sets the buffer portion to a default of b'0'. It also
decodes the returned bytestring to a Python3 string (utf-8).

It assumes the CLI is sending text only and that there is nothing in the
binary portion of the buffer that is returned from the librarian.

Copyright (c) 2020 by Jeff Bass.
License: MIT, see LICENSE for more details.

"""

import sys
import traceback
from time import sleep
from imagezmq import ImageSender

# open imageZMQ link to Librarian
# use any of the formats below to specifiy address of display computer
# sender = QuerySender(connect_to='tcp://localhost:5555')
# sender = QuerySender(connect_to='tcp://127.0.0.1:5555')
# sender = QuerySender(connect_to='tcp://jeff-macbook:5555')
# sender = QuerySender(connect_to='tcp://192.168.1.190:5555')

class QuerySender(ImageSender):
    def __init__(self, connect_to='tcp://*:5555', REQ_REP = True):
        ImageSender.__init__(self, connect_to=connect_to, REQ_REP = REQ_REP)
    def send_query(self, query, buf=b'0'):
        reply_b = self.send_jpg(query, buf)  # send_jpg returns a bytestring
        reply = reply_b.decode('utf-8')  # decode from bytes to Python 3 string
        return reply

def main():
    connect_to = 'tcp://localhost:5557'
    print('Default Librarian address is:', connect_to)
    query = input('Press enter to keep it, or enter a different one: _? ')
    if query:
        connect_to = query.strip()
    sender = QuerySender(connect_to=connect_to)
    send_query = sender.send_query
    try:
        print('CLI Chat with Librarian.')
        print()
        while True:
            try:
                query = input('_? ')
            except EOFError:
                sys.exit()
            reply = send_query(query)  # gets a byte string
            print(reply)
            print()
    except (KeyboardInterrupt, SystemExit):
        sys.exit()
    except Exception as ex:
        traceback.print_exc()
    finally:
        sender.close()
        sys.exit()

if __name__ == '__main__' :
    main()
