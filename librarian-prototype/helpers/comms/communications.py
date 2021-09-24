"""communications: communications classes and programs for librarian

In addition to defining various communication classes, some functions are
intended to be run as in separate standalone programs, with an appropriate
"__main__" clause. See CLI_chat.py as an example.

Copyright (c) 2018 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import csv
import sys
import pprint
import logging
import threading
from time import sleep
from pathlib import Path
from collections import namedtuple
from helpers.comms.gmail import Gmail
from imagezmq import ImageHub, ImageSender
from queue import Queue, Empty, Full
from collections import deque

logger = logging.getLogger(__name__)

class QueryReceiver(ImageHub):
    def __init__(self, open_port='tcp://127.0.0.1:5555', REQ_REP = True):
        ImageHub.__init__(self, open_port=open_port)
    def receive_query(self):
        query, buf = self.recv_jpg()
        return query  # may return buf (binary buffer) in further development

class CommChannel:
    """ Methods and attributes for a communications channel

    Sets up a single communication channel, by creating an input method
    that is specific to this channel using its settings. Then starts an
    input thread and an output thread specific to this channel.

    Each communications channel has its own unique versions of these 8 items:
        1. channel.query_q to hold queries from channel until needed by Librarian
        2. channel.reply_q to hold replies from Librarian to send via channel
        3. channel.next_query method that returns next item in queries queue
        4. channel.send_reply to send reply or new message via channel:
           - In reply to a query
           - To initiate a new conversation
             (Most conversations are started by a User; but sometimes Librarian
             will need to start a conversation, e.g., to send a timed reminder)
        5. Thread for fetching input and putting it into query queue
        6  Thread receiving output and putting it into output queue
        7. Sender_ID, if known by input method (None, if not)
        8. Sending program or process. For example, the CLI channel will need
           the user to start a "CLI_chat.py" program that uses ZMQ to send
           and receive messages. Sender programs are this same Communications
           module.

    Parameters:
        channel (str): Channel name from settings yaml communications section.
                       Example channels include gmail and CLI, but can also
                       include audio
        details (dict): Channel options & details specificed for this channel

    """
    def __init__(self, settings, comm_channel, details):
        # print('channel, details', channel)
        # pprint.pprint(details)
        self.query_q = None  # replaced with a specific queue by channel setup
        self.reply_q = None  # ditto
        if comm_channel.lower().strip() == 'gmail':  # set up gmail
            self.setup_gmail(settings, comm_channel, details)
        elif comm_channel.lower().strip() == 'cli':  # command line interface
            self.setup_cli(comm_channel, details)
        else:
            raise YamlOptionsError('Unknown comm channel in yaml file.')

    def next_query(self):
        """ next_query: return the next query to Librarian

        For each communication channel instance, this instance method gets
        the next query in the queue for the channel. This assumes that each
        channel must have a method or a thread that loads all inbound queries
        for that channel.

        Returns:
            next item from self.query_q OR None if self.query_q is empty
        """

        try:
            query = self.query_q.get(block=False)
        except Empty:
            return None
        else:
            return query

    def send_reply(self, reply):
        """ send_reply: push the reply from the Librarian onto reply queue

        This ia a placehoder method. It will be replaced with a channel
        specific method as each channel is initialized.

        Parameters:
            reply: reply from Librarian to be send back channel

        """
        pass  # this method will be replaced with channel specific methods

    def close(self):
        """ close the communications channel

        This is a placeholder method. It will be replaced with a chennel
        specific close method as each channel is initialized.

        """
        pass

    def setup_cli(self, comm_channel, details):
        """ setup_cli: set up the "8 items" for the CLI comm channel

        Parameters:
            comm_channel (dict): The dictionary holding options for CLI
            details (dict): indiviual options in comm_channel

        """

        # print the parameters to make sure they are what you think they are
        # print('Contents of comm_channel:')
        # pprint.pprint(comm_channel)
        # print('Contents of details:')
        # pprint.pprint(details)
        self.name = 'CLI'
        self.port = details.get('port', 5556)  # CLI ZMQ port
        maxsize = 2  # only need minimal queue for CLI
        # first, set up query queue and start a query thread
        self.query_q = Queue(maxsize=maxsize)
        self.address = 'tcp://127.0.0.1:' + str(self.port).strip()
        # print('CLI hub address is:', self.address)
        self.q_r = QueryReceiver(open_port=self.address)
        # start the thread receive CLI queries and put them into self.query_q
        t = threading.Thread(target=self.CLI_query_put)
        # print('Starting CLI threading')
        t.daemon = True  # allows this thread to be auto-killed on program exit
        t.name = 'CLI QueryReceiver'  # naming the thread helps with debugging
        t.start()
        # next, set up send_reply function specific to CLI.
        self.reply_q = Queue(maxsize=maxsize)  # queue for ZMQ REP replies
        self.send_reply = self.CLI_send_reply  # specific CLI_send_reply method
        # finally, set the specific close function for CLI
        self.close = self.q_r.close

    def CLI_query_put(self):
        """ CLI_query_put: receive query via QueryReceiver; put into self.query_q

        Receives inbound CLI query from CLI_chat.py which runs as a separate
        program. This methods runs in a Thread, loops forever and puts every
        query received into the Librarian query_q. Waits until reply has been
        sent (via ZMQ REP portion of REQ/REP cycle) before next receive_query.
        """
        while True:
            query = self.q_r.receive_query()  # will block until CLI query recvd
            self.query_q.put(query)
            # Need to block here until REP has been sent in CLI_send_reply
            self.OK = self.reply_q.get(block=True)  # wait for reply...
            # got the OK from CLI_send_reply so can fetch the next query

    def CLI_send_reply(self, reply):
        """ send_reply: push the CLI reply from the Librarian onto reply queue

        Because only one CLI sender / receiver can exist at a time on a single
        ZMQ port, there is no need for a reply queue. The reply is sent as the
        REP portion of the ZMQ REQ/REP message pair

        Parameters:
            reply: reply from Librarian to be sent back to the CLI channel

        """

        reply = reply.encode()  # convert string to bytes to make ZMQ happy
        self.q_r.send_reply(reply)  # sends reply via ZMQ REP
        self.reply_q.put('OK')  # having sent the ZMQ REP, put OK into reply_q
        #                    so that next REQ can be fetched in CLI_query_put()

    def setup_gmail(self, settings, comm_channel, details):
        """ setup_gmail: set up the "8 items" for the gmail comm channel

        Parameters:
            comm_channel (dict): The dictionary holding options for gmail
            details (dict): indiviual options in comm_channel

        """

        # print the parameters to make sure they are what you think they are
        # print('Contents of comm_channel:')
        # pprint.pprint(comm_channel)
        # print('Contents of details:')
        # pprint.pprint(details)
        self.name = 'Gmail'
        self.patience = settings.patience
        self.port = details.get('port', 5559)  # gmail ZMQ port
        maxsize = 200  # size of Queue specific to Gmail queries
        # first, set up query queue and start a query thread
        self.address = 'tcp://127.0.0.1:' + str(self.port).strip()
        # print('Gmail hub address is:', self.address)
        self.q_r = QueryReceiver(open_port=self.address)
        # start the process to receive gmail queries and put them into self.query_q
        self.query_q = Queue(maxsize=maxsize)
        t = threading.Thread(target=self.gmail_query_put)
        # print('Starting gmail query receiver thread')
        t.daemon = True  # allows this thread to be auto-killed on program exit
        t.name = 'Gmail QueryReceiver'  # naming the thread helps with debugging
        t.start()
        # Start python gmail.py to wath gmail & send inbound queries to above
        self.send_reply = self.gmail_send_reply  # set a specific gemail method
        # finally, set the specific close function for gmail
        self.close = self.q_r.close
        self.gmail = self.setup_gmail_sender(settings, details)

    def gmail_query_put(self):
        """ gmail_query_put: receive query via QueryReceiver; put into self.query_q

        Receives inbound gmail query from gmail_watcher which runs as a separate
        process. This methods runs in a Thread, loops forever and puts every
        query received into the Librarian query_q.
        """
        while True:
            query = self.q_r.receive_query()  # will block until gmail query recvd
            self.query_q.put(query)
            self.q_r.send_reply(b'OK')  # sends reply acknoledgment via ZMQ REP

    def setup_gmail_sender(self, settings, details):
        """ Instantiates a GMail instance to be used by gmail_send_reply().

        Parameters:
            settings (Settings object): holds the settings from the yaml file
        """
        gmail = None
        gmail_dir = settings.lib_dir / Path('gmail')  # gmail directory
        # self.contacts = details.get('contacts', 'contacts.txt')
        # details = {'contacts': 'contacts.txt', 'port': '5559'}
        contacts = self.get_contacts(gmail_dir, details)
        phones_OK_list = [contact.mobile_phone for contact in contacts]
        emails_OK_list = [contact.email for contact in contacts]
        # print('Phones:', *phones_OK_list)
        # print('Emails:', *emails_OK_list)
        # print('Instantiating Gmail().')
        # print()
        gmail = Gmail(settings, details, use_q_s=False)  # no QuerySender needed
        return gmail

    def gmail_send_reply(self, reply):
        """ send reply to gmail using gmail api

        """
        # print("Simulating sending a reply to gmail:", reply.split("|", 1)[0])
        self.gmail.gmail_send_reply(self.gmail.gmail, reply)
        return

    def get_contacts(self, gmail_dir, details):
        """Gets contacts from contacts data file

        Example lines from contacts.txt for reference
        name|full_name|canonical_name|mobile_phone|email
        Jeff|Jeff Bass|jeff_bass|8054697213|jeffbass@me.com

        Returns:
            contacts, a list of named tuples of contact info

        Example of extracting a single line
            [contact.mobile_phone for contact in contacts if contact.name=='Jeff']
            ['8054697213']
        """
        contacts_file = details.get('contacts', 'contacts.txt')
        contacts_file = gmail_dir / Path(contacts_file)
        # print('contacts file:', contacts_file )
        with open(contacts_file, 'r') as f:
            # read header line and set up namedtuple
            lines = csv.reader(f, delimiter='|')
            # fields = lines.next()  # field names list from first line in file
            fields = next(lines)  # field names list from first line in file
            Contact = namedtuple('Contact', fields)
            # read all lines in file, creating a named tuple for each line in file
            # if len(line) > 0 avoids TypeError due to any blank lines at end of file
            contacts = [Contact(*line) for line in lines if len(line) > 0]
        return contacts
