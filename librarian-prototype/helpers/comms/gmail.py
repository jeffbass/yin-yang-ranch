"""gmail.py: Fetch queries from gmail & send replies back

Contains Gmail class which initializes the Gmail service, and has a method to watch
the Gmail mailbox for any changes. When a change occurs, unread messages are
retrieved. If any of the unread messages are from senders in the contact list,
the text of the messages is sent to the libarian as a query, then the reply
from the librarian is sent as a Gmail reply.

Also contains a gmail_send_reply method to send librarian replies to Gmail.


Copyright (c) 2020 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import os
import csv
import sys
import base64
import pprint
import pickle  # used for storing / reading back credentials
import logging
from time import sleep
from pathlib import Path
from datetime import datetime
from collections import namedtuple
from helpers.utils import Patience
from multiprocessing import Process
from email.mime.text import MIMEText
from imagezmq import ImageHub, ImageSender
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

log = logging.getLogger(__name__)

class QuerySender(ImageSender):
    def __init__(self, connect_to='tcp://*:5555', REQ_REP = True):
        ImageSender.__init__(self, connect_to=connect_to, REQ_REP = REQ_REP)
    def send_query(self, query, buf=b'0'):
        reply_b = self.send_jpg(query, buf)  # send_jpg returns a bytestring
        return reply_b  # just 'OK' for gmail comm channel; don't need to use it

class Gmail:
    """ Initialize gmail API, read and write messages

    Sets up the Gmail service. Starts a Process() to watch Gmail for new
    messages and send the ones that are queries to Librarian via ZMQ. Provides
    a method to send replies back to Gmail service.

    Parameters:
        settings (str): settings & options from libarian.yaml.
        details (dict): channel options & details specificed for Gmail channel

    """
    def __init__(self, settings, details, use_q_s=True):
        # pprint.pprint(details)
        gmail_dir = settings.lib_dir / Path('gmail')  # gmail directory
        token = Path("token1.pickle")  # token1 when use_q_s=False
        self.token_file = str(gmail_dir / token)
        creds = Path("credentials.json")
        self.credentials_file = str(gmail_dir / creds)
        # Use QuerySender if this instance of Gmail is sending messages via ZMQ
        # Also use alternate directory and files for Gmail creds files
        if use_q_s: # set up QuerySender to send messages via ZMQ
            self.port = details.get('port', 5559)  # gmail ZMQ port
            self.address = 'tcp://127.0.0.1:' + str(self.port).strip()
            # print('Self address:', self.address)
            self.q_s = QuerySender(connect_to=self.address)
            gmail_dir = settings.lib_dir / Path('gmail2')  # gmail directory
            token = Path("token2.pickle")  # token2 when use_q_s=True
            self.token_file = str(gmail_dir / token)
            creds = Path("credentials.json")
            self.credentials_file = str(gmail_dir / creds)
        contacts = self.get_contacts(gmail_dir, details)
        self.phones_OK_list = [contact.mobile_phone for contact in contacts]
        self.emails_OK_list = [contact.email for contact in contacts]
        self.mail_check_seconds = details.get('mail_check_seconds', 5)
        self.patience = settings.patience

        self.gmail, self.historyId = self.gmail_start_service()

    def gmail_start_service(self):
        """ gmail_start_service -- start the gmail service using credentials

        Starts the gmail service using the 2 credential files (json and token).
        See Gmail API docs and quickstart.py for details. Reads a message to
        obtain a current historyId; used by gmail_monitor to watch
        for changes in the gmail mailbox; polling mailbox history is much
        cheaper in "points" than polling for new messages themselves.

        Returns:
            gmail: the Gmail service object with read, send, etc. methods.
            historyId: a current historyId

        """
        creds = self.get_credentials()
        # initialize gmail service
        gmail = build('gmail', 'v1', credentials=creds, cache_discovery=False)
        # get list of messages: first step in getting a historyId
        results = gmail.users().messages().list(userId='me',
            maxResults=10,includeSpamTrash=False).execute()
        num_msgs = results.get('resultSizeEstimate', -1)
        messages = results.get('messages', [])
        if not messages:
            latestMessageId = None
        else:
            # get the first message in the list which should be the latest
            latestMessageId = messages[3].get('id', None)
            latestMessageThreadId = messages[3].get('threadId', None)
        # print('Latest Message Id and Thread Id:')
        # print(latestMessageId, latestMessageThreadId)
        # print('Number of messages Estimate: ', num_msgs)
        # print('Number of messages in message list: ', len(messages))
        if not messages:
            pass
            # print('No messages retrieved')
        else:
            pass
            # print()
            # print('Received', len(messages), ' messages.')
            # print('list of messages:')
            # for message in messages:
            #    pprint.pprint(message)
            #    print()
        # messages().list() returns a list of message & thread ids
        # Id and threadId; if they are the same value
        # then message is the first message in a new thread
        # get a single message & get its historyId
        # results is a dict of all the fields of a single message; see API docs
        results = gmail.users().messages().get(userId='me',
            id=latestMessageId, format='minimal').execute()
        if not results:
            # print('No message retrieved')
            pass
        else:
            historyId = results.get('historyId', None)
            # print('Retrieval of message: ', latestMessageId, 'of thread: ',
            #    latestMessageThreadId)
            # pprint.pprint(results)
        return gmail, historyId

    def get_credentials(self):
        """Gets valid user credentials from token.pickle storage.

        If nothing has been stored, or if the stored credentials are invalid,
        the OAuth2 flow is completed to obtain the new credentials.
        The OAuth2 flow uses the Chrome browser; USE SDB broswer login!!!
                                              (Because we are reading SDB email)
        Returns:
            creds, the obtained credentials.
        """
        # If modifying these scopes, delete the file token.pickle.
        # Then, next get_credentials() will build new token with new SCOPES.
        SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

        creds = None
        # The file token.pickle stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        token_file = self.token_file
        credentials_file = self.credentials_file
        # print('Creds file names:')
        # print('    token:', token_file, ' type:', type(token_file))
        # print('    creds:', credentials_file, ' type:', type(credentials_file))
        if os.path.exists(token_file):
            with open(token_file, 'rb') as token:
                creds = pickle.load(token)
                # print('Pickled token loaded.')
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            # print('Doing creds refresh:')
            if creds and creds.expired and creds.refresh_token:
                # print('Doing Refresh Credentials Request:')
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    credentials_file, SCOPES)
                # print("Used existing credentials_file OK.")
                creds = flow.run_local_server(port=0)
            # Save the credentials for the next run
            with open(token_file, 'wb') as token:
                # print('Saving token.pickle file.')
                pickle.dump(creds, token)
        return creds

    def gmail_watcher(self, gmail, historyId, mail_check_seconds,
                      phones_OK_list, emails_OK_list):
        # By putting historyId into a list, it becomes mutable and holds updates
        history_list = [historyId]  # historyId will be updated by below
        next_page_token = ['emptyToken']  # token for getting 2nd page of results

        while True:    # forever loop watching gmail mailbox for changes
            if self.mailbox_changed(gmail, history_list, next_page_token,
                                    mail_check_seconds):
                # get new messages from gmail, but only the ones that are from
                # senders on our OK lists; others are skipped.
                new_messages = self.get_new_messages(gmail,
                               phones_OK_list,
                               emails_OK_list)
                # print('New messages:')
                # pprint.pprint(new_messages)
                if new_messages:   # there are some new messages
                    self.mark_as_read(gmail, new_messages)  # move to below send_query!
                    for message in new_messages:
                        # each message is a tuple of values from get_new_messages()
                        # create a query from the tuple that is string of pure text
                        query = "|".join(list(message))
                        # need to add Patience() code here to recover from
                        # network or librarian outages, similar to how
                        # imagenodes do.
                        REP = self.q_s.send_query(query)  # ZMQ REP b'OK'

    def mailbox_changed(self,gmail, history_list, next_page_token, mail_check_seconds):
        ''' Use history().list() to check for changes to mailbox

            Depending on how often the gmail api is "checked"
            it is possible for the multiple calls per minute to watch
            for new emails be very expensive. Using history().list() is better.

            Google has Usage Limits measured in Quota Units.
            messages().list() is 5 Quota Units and
            history().list() is 2 Quota Units (less than half price)
            drafts().send() is 100 Quota Units

            This function implements a forever polling loop checking
            history().list() for changes. Returns True when history
            has changed, meaning something in the mailbox has changed.
            There may be false positives (unimportant mailbox changes),
            but other functions check for valid / important messages.
            This function only watches for history().list() changes

        Parameters:
            gmail (service object): the Gmail service object
            history_list (list): list of historyId's. Update to newest one each loop.
            next_page_token (list): list whose 1st element is the nextPageToken
            mail_check_seconds (int): how often to check the gmail history list

        Returns:
            Boolean True if mailbox change; False if not
        '''
        startHistoryId = history_list[0]

        # users().history().list() requires a valid startHistoryId.
        # The startHistoryId was obtained by gmail_start_service().
        # print("startHistoryId: ", startHistoryId, "is type: ", type(startHistoryId))

        last_results = gmail.users().history().list(userId='me',
            startHistoryId=startHistoryId,
            maxResults=10).execute()
        i = 0    # number of history changes checks
        num_err_results = 0

        while True:  # loop forever until a there is a change in mailbox history
            # Do not check history more often than mail_check_seconds
            sleep(mail_check_seconds)
            try:
                results = gmail.users().history().list(userId='me',
                    startHistoryId=startHistoryId,
                    maxResults=10).execute()
            except Exception as ex:
                num_err_results += 1
                log.error("Error raised in gmail.history.list() num = " + str(num_err_results))
                results = last_results # set to last non-error results
                if num_err_results > 10: # too many; put into a variable?
                    raise  # raise the exception up to main handler
                else:   # wait for timeout type error to clear
                    sleep(10)  # need to edit this into a variable?
            i += 1
            if results == last_results:    # no mailbox history changes
                # print('Retrieved results #', i, ": No changes")
                pass
            else:    # some changes in history().list()
                # print('Retrieved results #', i, ": Some changes")
                # last_results = results
                nextPageToken = results.get("nextPageToken", "emptyToken")
                historyId = results.get("historyId", "emptyId")
                # print("nextPageToken: ", nextPageToken)
                # print("historyId: ", historyId)
                # set historyId and nextPageToken as new list elements
                history_list[0] = historyId  # save historId in list for next call
                next_page_token[0] = nextPageToken
                return True
            # print("No history changes pass ", i)

    def is_SMS(self, from_value):
        # check that this message has address form of a text message
        if ('@txt.voice.google.com>' in from_value
            and '(SMS)' in from_value
            and '<1' in from_value):
            return True
        else:
            return False

    def get_new_messages(self, gmail, phones_OK_list,
                         emails_OK_list, n=25):
        ''' gets some new messages from gmail messages.list()

        Parameters:
            phones_OK_list (list): list of phone numbers OK to receive from
            emails_OK_list (list): list of emails it is OK to receive from
            n (int): number of emails to retrieve in a batch

        '''
        # print("Fetching message list")
        results = gmail.users().messages().list(userId='me',
            labelIds=['UNREAD', 'INBOX'],
            maxResults=n).execute()

        message_list = []
        if 'messages' in results:
            message_list.extend(results['messages'])
        else:
            return None
        # print("Number of messages in results: ", len(message_list))
        if len(message_list) == 0:
            return None

        new_messages = []
        for message in message_list:
            msg_id = message.get('id', None)
            message = gmail.users().messages().get(userId='me',
                id=msg_id).execute()
            thread_id = message.get('threadId', None)
            labels = message.get('labelIds', None)
            message_internalDate = message['internalDate']
            message_datetime = datetime.fromtimestamp(int(int(message_internalDate)/1000))
            payload = message['payload']
            headers = payload['headers']
            # each header is a dictionary holding 2 tuples
            # each tuple is (header name, header value)
            # name and value are unicode strings
            for header in headers:
                name, value = header.items()
                name_str = str(name[1])
                from_str = u'From'
                subject_str = u'Subject'
                to_str = u'To'
                if (name_str == from_str):
                    from_value = value[1]
                elif (name_str == subject_str):
                    subject_value = value[1]
                elif (name_str == to_str):
                    to_value = value[1]
            # print("Debugging SMS:")
            # print("From:", from_value)
            # print("is_SMS value:", is_SMS(from_value))
            if self.is_SMS(from_value):
                # extract SMS sending phone number from "From" header
                num_start = from_value.find('<1') + 14
                num_end = num_start + 10
                sms_from = from_value[num_start:num_end]
                # print("sms_from: |" + sms_from + "|")
                if sms_from not in phones_OK_list:
                    continue
                message_text = message['snippet'][13:]
                text_end = message_text.find(" YOUR ")
                message_text = message_text[:text_end]
            else:    # a regular email; not SMS
                sms_from = None
                # print('Email from: ', from_value, type(from_value))
                if from_value not in emails_OK_list:
                    continue
                message_text = message['snippet']
            # print("message_text:", message_text)
            # line=line.decode('utf-8','ignore').encode("utf-8")
            # bytes(line, 'utf-8').decode('utf-8','ignore')
            # used encode to get rid of all non-ascii characters
            message_text = bytes(message_text, 'utf-8').decode('utf-8','ignore')
            # print('message_text:', message_text, 'type:', type(message_text))
            # replace snippet encoding of apostrophe
            # TODO Find out why can't find / replace &#39;
            message_text = message_text.replace("&#39;", "'")
            # append message tuple to new_messages, message_text first
            new_messages.append((message_text, msg_id, thread_id,
                            from_value, subject_value,
                            to_value, sms_from),)

        return new_messages

    def mark_as_read(self, gmail, new_messages):
        """ Mark gmail messages as read by removing UNREAD label

        Parameters:
            gmail (service object): gmail service object
            new_message (list): list of messages to be marked as "READ"
        """
        if new_messages is None:  # no messages to mark
            return
        for message in new_messages:
            msg_id = message[1]
            gmail.users().messages().modify(userId='me',
                id=msg_id,body={'removeLabelIds': ['UNREAD']}).execute()

    def gmail_send_reply(self, gmail, reply_str):
        """ gmail_send_reply: send reply from the Librarian back via gmail

        This function is called from the librarian main loop.

        It sends a single query reply back via gmail. Each query sent to the
        librarian from gmail has header info appended to the text of the
        message. This gmail reply sender uses that header info to reply to the
        correct messageId, threadId, etc.

        Structure of reply_str:
          reply_text|msg_id|thread_id|to_value|subject_value|from_value|sms_from
          (note that to_value and from_value are swapped from original message)
          (reply protocol requires this swapping pattern to draft a reply)

        Parameters:
          gmail (Gmail service object): Gmail service object for Gmail API
          reply (str): reply from Librarian to be sent back via gmail

        """
        # First parse the reply into message text and gmail threadid, etc.
        reply = reply_str.split('|')  # reply is list of reply parts in reply_str
        # then load the draft reply and send it
        threadid = reply[2]  # thread being replied to
        to_send = MIMEText(reply[0])  # text of reply created by librarian
        # to_send = reply[0]  # text of reply created by librarian
        to_send["To"] = reply[3]  # replying to (whick was from_value in msg)
        to_send["Subject"] = reply[4]  # replying to subject
        to_send["From"] = reply[5]  # replying from (which was to_value in msg)
        # example: bytesThing = stringThing.encode(encoding='UTF-8')
        raw = base64.urlsafe_b64encode(to_send.as_string().encode(encoding='UTF-8'))
        raw = raw.decode(encoding='UTF-8')  # convert back to string
        message = {'message': {'raw': raw, 'threadId': threadid}}
        draft = gmail.users().drafts().create(userId="me", body=message).execute()
        draftid = draft['id']
        gmail.users().drafts().send(userId='me',
                body={ 'id': draftid }).execute()

    def gmail_send_SMS(self, phone_number, message_text):
        """ gmail_send_SMS: send SMS text message via Gmail

        It sends a single SMS text message. For security and other reasons, this
        does not send a Gmail meessage. Instead it searches for a GMail
        SMS message from the phone number. Then composes a reply_str. Then


        Structure needed for reply_str:
          reply_text|msg_id|thread_id|to_value|subject_value|from_value|sms_from
          (note that to_value and from_value are swapped from original message)
          (reply protocol requires this swapping pattern to draft a reply)

        Parameters:
          phone_number (str): phone number to send text message to
          message (str): message to send to phone_number

        """
        # use phone number to search for Gmail SMS messages from that number
        gmail = self.gmail
        p = phone_number.strip()
        area_code = p[0:3]
        first_3 = p[3:6]
        last_4 = p[6:10]
        search = ' '.join(['SMS', area_code, first_3, last_4])
        # print('Search String Parts:')
        # print('  area_code:', area_code)
        # print('    first_3:', area_code)
        # print('     last_4:', area_code)
        # print('Search string for Gmail:', search)
        results = gmail.users().messages().list(userId='me',
            maxResults=10,includeSpamTrash=False,q=search).execute()
        num_msgs = results.get('resultSizeEstimate', -1)
        messages = results.get('messages', [])
        num_messages = len(messages)
        # print('Number of messages from Gmail SMS number query', num_messages)
        if not messages:
            latestMessageId = None
        else:
            # get the first message in the list which should be the latest
            latestMessageId = messages[0].get('id', None)
            latestMessageThreadId = messages[0].get('threadId', None)
            msg_id = messages[0].get('id', None)
            message = gmail.users().messages().get(userId='me',
                id=msg_id).execute()
            thread_id = message.get('threadId', None)
            labels = message.get('labelIds', None)
            message_internalDate = message['internalDate']
            message_datetime = datetime.fromtimestamp(int(int(message_internalDate)/1000))
            payload = message['payload']
            headers = payload['headers']
            # each header is a dictionary holding 2 tuples
            # each tuple is (header name, header value)
            # name and value are unicode strings
            for header in headers:
                name, value = header.items()
                name_str = str(name[1])
                from_str = u'From'
                subject_str = u'Subject'
                to_str = u'To'
                if (name_str == from_str):
                    from_value = value[1]
                elif (name_str == subject_str):
                    subject_value = value[1]
                elif (name_str == to_str):
                    to_value = value[1]
            # print("Debugging SMS:")
            # print("From:", from_value)
            # print("is_SMS value:", is_SMS(from_value))
            # print("message_text:", message_text)
            # line=line.decode('utf-8','ignore').encode("utf-8")
            # bytes(line, 'utf-8').decode('utf-8','ignore')
            # used encode to get rid of all non-ascii characters
            # message_text = bytes(message_text, 'utf-8').decode('utf-8','ignore')
            # print('message_text:', message_text, 'type:', type(message_text))
            # replace snippet encoding of apostrophe
            # TODO Find out why can't find / replace &#39;
            # message_text = message_text.replace("&#39;", "'")
            # append message tuple to new_messages, message_text first
            if 'SMS' in to_value:
                to_value, from_value = from_value, to_value
            time_str = datetime.now().strftime("%I:%M %p").lstrip("0")
            message_text = message_text + " (" + time_str + ")"
            message_tuple = (message_text, msg_id, thread_id,
                            from_value, subject_value,
                            to_value, search)
            msg_string = "|".join(list(message_tuple))
        # print("The message string with msg_id, thread_id, etc:")
        # print(msg_string)
        self.gmail_send_reply(gmail, msg_string)

    def close(self):
        """ close: close the QueryReceiver ZMQ port and context
        """
        self.q_r.close()

    def get_contacts(self, gmail_dir, details):
        """Gets contacts from contacts data file

        Example lines from contacts.txt for reference
        name|full_name|canonical_name|mobile_phone|email
        Jeff|Jeff Bass|jeff_bass|8885551212|jeff@yin-yang-ranch.com

        Returns:
            contacts, a list of named tuples of contact info

        Example:
            >>> [contact.mobile_phone for contact in contacts if contact.name=='Jeff']
            ['8885551212']
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

    def fix_comm_link(self):
        """ Evaluate, repair and restart communications link with librarian.

        Restart link if possible, else restart program.
        """
        # TODO add some of the ongoing experiments to this code when it has
        #     progressed in development and testing
        # Current protocol:
        #     just sys.exit() for now.
        #     Because this program is started
        #     and restarted by systemd as a service with restart option on, it
        #     will restart the program with a delay and try communicating again.
        #     It will be logged in systemctl journald.
        #
        # Other ideas that might be worth trying:
        #     1. Just wait longer one time and try sending again
        #     2. Doing 1 repeatedly with exponential time increases
        #     3. Stopping and closing ZMQ context; restarting and sending
        #            last message
        #     4. Check WiFi ping; stop and restart WiFi service
        #
        raise KeyboardInterrupt
