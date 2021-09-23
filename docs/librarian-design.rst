=============================================================
The Librarian program design, pseudo code and data structures
=============================================================

Introduction
============

The **librarian** is the program at the heart of the yin-yang-ranch system. It
acts as the "ranch hand" assistant in our Yin Yang Ranch setup. It acts
as a librarian would be expected to. It has access to information that
is on file, and answers questions about it.
The main user interface to the **librarian** is a "chat"
capability that can answer simple questions about events and images gathered
by the **imagenodes**.

.. contents::

Overview of the Librarian beyond the prototype
==============================================

The **librarian** prototype has limited functionality. It can:

- Receive and reply to queries from a simple terminal CLI interface
- Receive and reply to queries via SMS text messages sent to a Google Voice number
- Answer questions about current **imagenode** status (e.g., Is the water flowing?)
- Include information about a previous state ("water is off; last time flowing was 5:03pm").
- Answer questions about sensor readings ("Inside temperature?")
- The **librarian** prototype uses the Linux ``tail`` utility to continually add
  new events as they are added in the **imagehub**.

All of the **librarian** prototype capbilities involve answering questions about
recent events in the **imagehub** events log.

There are additional **librarian** capabilities in development & testing:

- Answer questions about objects seen ("vehicles today?")("Coyotes?")
- Answer questions about history, including summaries ("How many coyotes seen
  in the last week?") ("What was the average high temperature this month?")
- Track the event logs of multiple **imagehubs** running on multiple computers
  (the prototype only watches a single **imagehub** running on the same
  computer as the **librarian**)

The librarian does not do any image analysis or object detection. It reads
image / object label files that are written by object detection programs that
continuously scan the images in the **imagehub** as they are written. The object
detection programs run on a separate computer. They read the **imagehub** image
files, do object detection on those files and then write description labels to
files that are in the ``librarian_data`` directory. An example of a
``detected-objects.txt`` file is in the ``test-data`` folder in this repository.
The **librarian** uses these detected object label files to answer questions
about what objects have been seen and when.

Librarian Pseudo Code outline and Classes
=========================================

Here's what **librarian** does in pseudo code::

  # Things are done one time at program startup:
   Read a  librarian YAML file into Settings (imagehub file locations, gmail credentials, etc.)
   Instantiate a Librarian using Settings:
     Instantiate all CommChannel's (includes CLI, Gmail, etc.)
     Do a system self check and log the result
     Start threads and subprocesses:
       Start a watching thread for each comm channel (e.g., gmail_watcher.py)
       Start a watching thread that processes new data as it is saved by imagehubs
       Start a scheduling thread that runs scheduled tasks like backups
       Start a HealthMonitor subprocess that watches the librarian, imagehubs and imagenodes for issues

   # The main Librarian forever loop:
   Response Loop forever:
     Receive a QueryRequest (from in_q which is loaded by an inbound CommChannel thread)
     Optionally, take an action (e.g., set barn_cam to no_motion)
     Compose a Reply (using data that was processed from the imagehub files)
     Send Reply (put into out_q which will be sent in an outbound CommChannel thread)

The Librarian communications, data handling and other modules are
located in the "helpers" directory. Here are the main Librarian Classes::

  Class Settings (filled once by reading from the YAML file)
  Class HealthMonitor (methods that monitor system and network health; does backups)
  Class Librarian (instantiated once using Settings)
    Class CommChannel (instantiated once per comm channel like Gmail or CLI)
      Class Gmail (instantiated once; fetches and sends messages via Gmail API)
      (other comm channels yet to be written, like Twilio SMS)
    Class Chatbot (instantiated once; receives queries and composes replies)
    Class HubData (instantiated once; provides HubData, e.g. events, to ChatBot)
    Class Schedule (instantiated once; starts scheduled tasks and methods)

Helper programs that interact with Libarian::

  - CLI_chat.py: A CLI program that sends queries to Librarian and prints
    responses to standard output (typically the terminal). The CLI_chat.py
    program is located in the comms folder. It is mainly used for testing.
  - gmail_watcher.py: a Python program that watches Gmail for new messages and
    sends a selected subset of them to the librarian via QuerySender ZMQ class.
  - Communications programs being developed include a Twilio SMS texting comm
    program and a website update program
  - HealthMonitor programs are being developed that watch **imagenodes**,
    **imagehubs** and the **librarian** for failures, restarting processes,
    programs and computers as needed.

Use of simple text and image files rather than a database
=========================================================

One design feature of the **librarian** is that it does not use any formal
database. Instead it uses simple text files (like the **imagehub** event logs)
to store data. These simple text files are read on an as-needed basis into
Python data structures in program memory. Image files are kept in
directories that are nested by date. The image content and object label files
that are created from the images are also kept in simple text files. The
computer's file system itself is the "database" of the **librarian**.

Messaging protocol for messages sent to & from the Librarian
============================================================

Each communication channel (such as gmail or CLI) has a separate thread or
subprocess to wait for incoming communication and send responses.
The Librarian uses ZMQ to communicate with each communication channel. For now,
it uses imageZMQ (as is done by the imagenode and imagehub programs). How this
is done varies by Commmunication Channel (such as Gmail channel vs. CLI
channel).

All messages to and from the Librarian will have the following format::

  (text, binary_buffer)

The first part is a text string with multiple fields separated by "|" character.
The second part is a binary buffer that can be any of:

1. An empty buffer with only a single byte as a place holder.
2. A jpg_buffer that contains a compressed image in jpg format.
3. Any other binary data that has been placed into a buffer, such as an
   audio snippet.

The advantage of using a tuple of (text, binary_buffer) is that every message
can (optionally) include a non-text portion, such as a jpg image or an audio
clip. By requiring EVERY message to or from the Librarian to use this
tuple format, there is no need for an if statement about message type (text
only or binary only or text and binary). When the binary portion is unneeded,
a single byte bytearray is used as a placeholder.

The text portion of each message is either simple text OR text followed by
one more more text fields that specify things like sender or messageId that
will influence composing the reply or routing the reply::

  Text of Message | Optional Data Field 1 | Optional Data Field 2 | etc.
  This is an Example of a text message with no optional data fields
  Gmail reply needs|msg_id|thread_id|to_value|subject_value|from_value|sms_from

Details (such as ZMQ port numbers) for each channel are specified in the
``librarian.yaml`` file.

Some messaging details are specific to a particular channel:

1. **CLI channel**: CLI design is simpler than other channels in that it uses only
one inbound ZMQ REQ/REP messaging socket for both inbound and outbound messages.
Waiting for inbound ZMQ message is done in a thread that puts each inbound
message (text only) into the self.query_q that is read by the librarian main
loop. The reply composed by the librarian is then sent back as the REQ/REP
message's REP portion. This means that there can be only 1 CLI sender / receiver
client at a time. That means that each CLI must be closed before any second
conversation can be started via the CLI channel.
Since the CLI channel is only used for testing and development, this is
"good enough". Having more than one CLI conversation at a time would require
an outgoing ZMQ REP/REQ message pair in addition to the inbound REQ/REP pair.
The CLI channel uses a separate CLI_chat.py python program that is run in the
terminal to start and manage the user side of the chat. Settings can be given
for tcp address and port number. The default is the tcp address of the localhost,
which assumes the CLI_chat program is being run on the same computer as the
librarian program. But any computer that can reach the librarian with a
standard "tcp:port" address could be used.
   There is a small "test program that simulates the Librarian" so the the
CLI_chat.py can be more easily tested. It is named CLI_chat_echo_test. It uses
the imageZMQ Hub class, so it needs to be started before the CLI_chat.py program.
Both of these communication programs are in the libarian/helpers/comms folder
in this git repository. They include 2 test classes QueryHub and QuerySender
which inherit from and add new methods to ImageHub and ImageSender imported from
imageZMQ.

2. **Gmail channel**: The current design uses the Python Gmail API, as
modeled by their "quickstart.py" program in the Gmail documentation. There is
a onetime setup of the Gmail service, then all calls are to the gmail service.
For example, here is the code to read a Gmail message::

  message = gmail.users().messages().get(userId='me',id=msg_id).execute()

A separate Python program, ``gmail_watcher.py``
is started to watch Gmail for new SMS text messages from Google Voice. When
there are new messages, these are read and filtered for messages from the
contacts list. The contacts list contains names, phone numbers for inbound SMS
text messages and email addresses for inbound email. If a message is from a
sender on the list, the message text is appended with gmail threadId and other
data and the query sent to the librarian inbound message queue using ZMQ. The
librarian composes a reply and the gmail.send_reply() method sends it via Gmail
using the appended threadId, etc. to route the message. Gmail's own message
history and threads are used to organize and store messages; the librarian does
not keep message history (which would be an unnecessary duplication of Gmail's
own very effective database). The contacts list is kept in contacts.txt file
in the librarian_data directory. It's format is simple and detailed in the
get_contacts() method in the Gmail class.

Image analysis, object detection and label handling
===================================================

As mentioned earlier, the **librarian** does not do any image analysis, object
detection in images or related work. Instead, the **librarian** expects files
to be written and updated by multiple image analysis programs, often running
on different computers. These programs read the images from the **imagehub**
image directories, perform analysis and object detection and then write one line
of text for each object detected to a ``detected-objects.txt`` file, which
contains all the details of time, image, object name & ID, bounding box corners,
etc. An example of a ``detected-objects.txt`` file is in the ``test-data``
folder in this repository.

My current object detectors are very simple and are modeled on programs that
have appeared in the OpenCV blog and the PyImageSearch blog. One great example
is this PyImageSearch blog post about labelling objects in a live video stream:
`Detecting dogs, persons and cars <https://www.pyimagesearch.com/2019/04/15/live-video-streaming-over-network-with-opencv-and-imagezmq/>`_
(and as a bonus, the blog post uses my own imageZMQ package for sending and
receiving images). Many of these programs are easily adapted to write object
labels to a text file. My current object detection programs are mashups of Python
and bash workflows. When I have cleaned them up and documented them, I will push
them to their own GitHub repositories.

Improving the query / request parsing
=====================================

The **librarian** currently uses a very simple "cascading-if-statements"
algorithm for parsing queries. The query "language" will always be simple
compared to general purpose digital assistants. But the query language can
be modeled as a Domain Specific Language (DSL) and then parsed with a more formal
lexical analyzer and parser. These are currently under development. The
current simple parser is contained in the ``chatbot.py`` module in the ``comms``
folder in the ``helpers`` folder. The parser is "hard-wired" with location words
like "barn", "back deck", etc. Building a formal DSL and associated parser will
be a big improvement.

`Return to main documentation page README.rst <../README.rst>`_
