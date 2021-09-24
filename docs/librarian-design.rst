===================================================================
The Librarian program design, pseudo code and a development roadmap
===================================================================

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

Overview of the Librarian development beyond the prototype
==========================================================

The **librarian** prototype has limited functionality. It can:

- Receive and reply to queries from a simple terminal CLI interface
- Receive and reply to queries via SMS text messages sent to a Google Voice number
- Answer questions about current **imagenode** status (e.g., Is the water flowing?)
- Include information about a previous state ("water is off; last time flowing was 5:03pm").
- Answer questions about sensor readings ("Inside temperature?")
- The **librarian** prototype uses the Linux ``tail`` utility to continually add
  new events as they are added in the **imagehub**. The **librarian** is limited
  to watching the event log of a single **imagehub** running on the same
  computer as the **librarian**.

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
files that are in the ``librarian_data`` directory. The **librarian** uses these
detected object label files to answer questions about what objects have been
seen and when. The **librarian** prototype in this repository does not have a
capability for reporting on detected objects.

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

Librarian main program is simple event loop for user queries
============================================================

The **librarian** main program is a simple event loop that watches for and responds
to user queries. Here is the Librarian main program.

.. code-block:: python

  def main():
      try:
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

Each request is tagged by the sender, communication channel, thread and message
IDs, etc. After the chatbot has composed a reply using available data, it uses these
tags to route the reply appropriately. The system can handle multiple
simultaneous senders and messages using ZMQ message queues to manage
concurrency. It works in much the same way as having multiple imagenodes
sending to a single imagehub. It works fine for up to a dozen senders, but
would get slow at a higher numbers of senders.

An alternative is to use a Python package such as Flask to manage messaging.
It would probably scale to a higher number of senders.

The Librarian uses text and image files rather than a database
==============================================================

One design feature of the **librarian** is that it does not use any formal
database. (Depending on your point of view, this might be a design flaw instead
of a design feature ;-) Instead of using a database, the **librarian** uses
simple text files (like the **imagehub** event logs) to store data and
communicate between programs. These simple text files are read on an as-needed
basis into Python data structures in **librarian** program memory. Image files
are placed by the **imagehub** in directories that are nested by date. The image
object label files that are created from the images are also kept in simple text
files.

The Yin Yang Ranch overall design reflects my own personal "bias of familiarity".
I have been using Unix utilities as filters for workflow pipelines of text files
for 50 years. For the Yin Yang Ranch sparse data matrix, a “graph” data structure
is optimal. The Unix OS file system is a "graph" tree database with a root (/)
node. Everything is a branch from the root. And there is a Unix common practice:
don’t use dedicated database software unless you really need to; for many
projects you can use the Unix OS file system as a database. The Unix file system
is very hardened & reliable & just as ACID as any other database (if you use it
the way it is designed to be used).

The **librarian** is part of a "mostly text" pipleline data flow::

 imagenodes —> imageZMQ —> imagehub -> events_text_files -> librarian -> SMS_texts
                               |                                ^
                          image_files                 detected_objects_files
                               v                                ^
                               |-----> object_detectors ------->|

The ``object_detector`` programs read the image_files from the **imagehub**
data directories and produce ``detected_objects_files`` that can be used by the
**librarian** to answer queries. (The **librarian** prototype version in this
GitHub repository does not read ``detected_objects_files``).

The Librarian uses native Linux utilities to perform common functions
=====================================================================

Native Linux utilities are very optimized and very fast. In a number of cases,
they are much faster than a Python alternative. Calling these native utilities
accomplishes many of the **librarian**'s functions as a separate subprocesses.
Here are a few examples.

``tail``: This Linux utility gets the last few lines from a text file. It does
does this very efficiently (without reading the entire file) and works fine on
a text file that is still being appended to by another program. The **librarian**
uses a subprocess to call the ``tail`` utility to grab the most recent
**imagehub** event log lines as they are being added. See the ``log_tail``
method in the ``data_tools.py`` module in the ``helpers``.

``rsync``: This Linux utility can copy files and directories from one computer
to another in a "smart" way that only copies changes. It is one of the most
powerful Linux utilities. It can update only the parts of a text file that have
changed. I use it for backups of all my **imagehub** and **librarian** data.
Here is what a archive style incremental backup of the **imagehub** data to
an external drive looks like::

  $ rsync -a imagehub_data/ /media/jeffbass/Linux250/imagehub_data


``systemctl``: This Linux utility is used to launch **imagenodes**, **imagehubs**,
the **librarian**, the comm agents like ``gmail_watcher.py`` and the various
object detectors that analyze the images written by the **imagehub**. It allows
the **librarian** HealthMonitor programs to restart **imagenodes** that are
hung or behaving badly. An example of this use is in the
``nodewatcher.py`` module in the ``helpers`` folder.

My own current workflow is a mashup of Python programs and bash / terminal
commands that allow me to look at logs and images on my Mac screen using its
QuickLook capability in the Finder. Some of these things will be incorporated
into future versions of the **librarian**. Here are a couple of examples.

ssh of **imagehub** logs to current my Mac::

  $ ssh 192.168.86.71 "cat /home/jeffbass/imagehub_data/logs/*log.2021-09-21 /home/jeffbass/imagehub_data/logs/*log"

This allows me to review an **imagehub** log in real time, even when it the
**imagehub** is running on another computer.

scp of selected images from **imagehub** to my Mac::

    $ scp 192.168.86.71:/home/jeffbass/imagehub_data/images/2021-09-21/[^W]*T1* .

This allows me to copy some recent imgage files (but excluding the WaterMeter)
to my Mac and then view them using the Mac Finder's QuickLook utility. A great
way to do a quick scan of recent images from the cameras.

Messaging protocol for messages sent to & from the Librarian
============================================================

Each communication channel (such as gmail or CLI) has a separate thread or
subprocess to wait for incoming communication and send responses.
The Librarian uses ZMQ to communicate with each communication channel. For now,
it uses imageZMQ (as is done by the imagenode and imagehub programs). How this
is done varies by Commmunication Channel (such as Gmail channel vs. CLI
channel).

All messages to and from the Librarian have the following format::

  (text, binary_buffer)

The first part is a text string with multiple fields separated by "|" character.
The second part is a binary buffer that can be any of:

1. An empty buffer with only a single byte as a place holder.
2. A jpg_buffer that contains a compressed image in jpg format.
3. Any other binary data that has been placed into a buffer, such as an
   audio snippet.  Listening for "coyote howls" and other sounds is an
   ongoing experiment that involves developing "audionode" modules for
   RPi's that is analogous to **imagenode**s.

The advantage of using a tuple of (text, binary_buffer) is that every message
can (optionally) include a non-text portion, such as a jpg image or an audio
clip. By requiring EVERY message to or from the Librarian to use this
tuple format, there is no need for an if statement about message type (text
only or binary only or text and binary). When the binary portion is unneeded,
a single byte ``bytearray`` is used as a placeholder.

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

As mentioned earlier, the **librarian** does not do any image analysis or object
detection in images or related work. Instead, the **librarian** expects files
to be written and updated by multiple image analysis programs, often running
on different computers. These programs read the images from the **imagehub**
image directories, perform analysis and object detection and then write one line
of text for each object detected to a ``detected-objects.txt`` file, which
contains various details of time, image, object name & ID, bounding box corners,
etc. The **librarian** prototype in this repository does not have a
capability for reporting on detected objects.

My current object detectors are quite simple and most of them are modeled on
programs that have appeared the PyImageSearch blog. One great example
is this PyImageSearch blog post about labelling objects in a live video stream:
`Detecting dogs, persons and cars <https://www.pyimagesearch.com/2019/04/15/live-video-streaming-over-network-with-opencv-and-imagezmq/>`_
(and as a bonus, the blog post uses my own imageZMQ package for sending and
receiving images). Many of these programs are easily adapted to write object
labels to a text file. My current object detection programs are mashups of Python
and bash workflows. They currently require a lot of manual tweaking and tuning.
When I have cleaned them up and documented them, I will push them to their own
GitHub repositories.

I know I mentioned this in the README, but it is worth mentioning again. I have
found **PyImageSearch.com** to be the best resource for learning how to build
computer vision programs in Python. It contains blog posts demonstrating many
different object detection techniques. Adrian Rosebrock provides easy to follow
explanations and detailed code Examples of many computer vision techniques
can be found
at `PyImageSearch.com <https://www.pyimagesearch.com/>`_. Highly recommended.

Improving the query / request parsing using graph trees
=======================================================

The **librarian** prototype uses a very simple "cascading-if-statements"
algorithm for parsing queries. The query "language" will always be simple
compared to general purpose digital assistants. But the query language can
be modeled as a Domain Specific Language (DSL) and then parsed with a more formal
lexical analyzer and parser. These are currently under development. The
current simple parser in the **librarian** prototype is contained in the
``chatbot.py`` module in the ``comms`` folder in the ``helpers`` folder. The
parser is "hard-wired" with location words like "barn", "back deck", etc.
Building a formal DSL and associated parser will be a big improvement.

In the next **librarian** version (currently in development), "request context"
is part of the query parsing process. This is used to build an in-memory "graph
data" structure that links "request context" with other query relationships. I
am using the Python
`networkx package. <https://networkx.org/documentation/stable/tutorial.html>`_
for building a query structure and finding matches with the "available data"
graph structure. An alternative would be to use more advanced Natural Language
Processing (NLP) techniques to parse requests and compose replies, but the
simple requirements of the **librarian** don't need anything that complex.

Where the Librarian design is going...a Roadmap / Wishlist for the Future
=========================================================================

The **librarian** roadmap for the future reflects my own needs. What questions
do I need to ask to help manage my small farm? The design of **librarian** is
evolving and it will likely never be "done". This is more of a dream list than
a roadmap, since I am unlikely to ever get all of these things coded.

- The ability to send images in text messages. The **librarian** prototype can
  only send text and not images. Sending images in SMS text messages
  is possible using Twilio, but I have done any work on this yet. ("Person seen
  in driveway. Image attached.")
- The ability to spot patterns and report on them. Especially regarding water
  usage. ("Water usage today was higher than for the last 7 days.")
  ("Water flowing in the last 2 hours is consistent with previous usage for
  watering the avocados.")
- The ability to report history in more general ways. ("Coyotes were seen 3
  times in the last week. Weekly average is 2.")
- What specific vehicles were seen. ("The mail truck was seen in the driveway
  at 4:15pm.")
- Where I might need to water based on analysis of images of plants. ("The
  leaves of fig tree are drooping.")
- Common patterns seen across different cameras. ("Amazon truck seen in driveway
  and front sidewalk area. Person seen in front sidewalk area.")

`Return to main documentation page README.rst <../README.rst>`_
