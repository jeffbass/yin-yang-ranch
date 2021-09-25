===============================================================
A simple prototype of the Librarian and Communications Programs
===============================================================

Introduction
============

The **librarian** is the program at the heart of the yin-yang-ranch system. It acts
as a librarian would be expected to. It keeps track of lots of information that
is on file, and answers questions about it. It also creates summary files, does
backups and checks that all the other systems are working OK. Most of the
information that the **librarian** keeps track of is the data that is sent by
**imagenodes** to **imagehubs**, including images, sensor readings and event
messages There are also some programs to monitor **imagenode** health.

.. contents::

Overview of the Librarian prototype
===================================

The **librarian** prototype has limited functionality. It can:

- Receive and reply to queries from a simple terminal CLI interface
- Receive and reply to queries via SMS text messages sent to a Google Voice number
- Answer questions about current **imagenode** status (e.g., Is the water flowing?)
- Include information about a previous state ("water is off; last time flowing was 5:03pm").
- Answer questions about sensor readings ("Inside temperature?")

For example, here is a text message exchange with "Susan", my librarian bot:

.. image:: ../images/text-messaging.png

That is a screen shot from a phone that had texted the "Susan" Google Voice phone
number that was being watched by the **librarian** prototype. The **librarian** code
that is in this repository was running and generated the responses shown in the
screen shot. The **librarian** was running on the same Linux computer that was
running the **imagehub** for 12 **imagenodes**.

Librarian Prototype Capabilities & Communications Channels
==========================================================

The **librarian** prototype is run on a computer that is also running an
**imagehub** program. The **librarian** acts as a "ranch hand" assistant in our
Yin Yang Ranch setup. The main user interface to the **librarian** is a "chat"
capability that can answer a few simple questions. The prototype can only answer
questions about the data from one **imagehub**.

The **librarian** prototype implements 2 communications channels: 1) SMS texting
(using Google Voice and its Gmail interface) and 2) a terminal window CLI text
interface.

The **librarian** prototype also has a "scheduled SMS text message" capability
which I use to have it send reminder texts for things like changing the
rechargeable battery in a remote **imagenode** camera. You can see an example
of how to set up "scheduled SMS text messages" in the ``librarian.yaml`` file.

This **librarian** prototype is incomplete and buggy. It is included in this
repository to convey an understanding of one possible design. It is
not ready for production use (although I have been running a version of it on
my ranch for about 3 years). This code is the basis for the **librarian** version
I am currently developing to push to its own GitHub repository when it is
more complete and it has a broader set of capabilities.

If you do want to experiment with the **librarian** prototype, here are some
hints to help you install and run it. But please remember that it is
experimental...so expect issues.

Also, the "location words" like "barn" and "deck" are hard-wired directly into
the code of chatbot.py in the ``comms`` folder. Similarily, the sensor words
like "temperature" are hard-wired into the same program. This will be changed
in future development, but for now, you can test the **librarian** using the the
test data in the ``test-data`` folder of this repository. That event data
includes the keywords that are hard-wired into the chatbot.py module. If you
want to use the **librarian** prototype with your own event logs, you will need
to change the ``location words`` and the ``observation words`` to match your own
event data.

I am continuing to develop the **librarian** prototype and expect to push a
more complete version to its own GitHub repository (with more detailed
installation, setup and testing information) at some time in the future.
Timing is uncertain as other priorities around the ranch (and my retirement
life!) keep pushing out the ongoing refactoring and development. I have a
working Librarian development design that includes a list of desired goals and
features in
`Librarian Design and Development Goals <librarian-design.rst>`_.
That design is a roadmap for ongoing development of the Librarian, the
Communications modules and Image Analysis.

Dependencies and Installation for the Librarian Prototype
=========================================================

The **librarian** prototype has been tested with:

- Python 3.6 and 3.7
- OpenCV 3.3 & 4.0+
- imagezmq 1.1.1
- imagehub 0.2.0

The **librarian** prototype code is in this repository. Get it by
cloning this GitHub repository::

    git clone https://github.com/jeffbass/yin-yang-ranch.git

Once you have cloned **librarian** to a directory on your local machine,
you can run some tests using the instructions below.

Data directories and files required by the Librarian
====================================================

The **librarian** requires data files from an **imagehub** running on the same
computer. Although the imagehub does not need to be running for the **librarian**
to run, the ``imagehub_data`` directories and files must be present. The
primary function of the **librarian** prototype is to answer questions about
the events in the **imagehub** event logs via ``CLI_chat`` or SMS text
messages. For testing purposes, there is an ``imagehub_data`` directory loaded
with examples from my own ``imagehub_data`` files. It is located in the
``test-data`` directory in this GitHub repository. For a further description of
the files created by the **imagehub** see
`imagehub: Receive and Store Images and Event Logs. <https://github.com/jeffbass/imagehub>`_

The **librarian** also some data files of its own. In this prototype, only the
minimum required data files are in ``test-data/librarian_data``. They include
2 gmail directories containing Gmail API credentials and an example contacts.txt
file in those same directories. If you want to try getting the SMS texting via
Google Voice / Gmail, then you will need to use this setup as a template.

Running the Librarian Prototype using CLI_chat.py
=================================================

The easiest way to run the **librarian** prototype is to run the terminal
CLI chat program to send queries. It requires running ``librarian.py`` to
listen for queries and compose responses AND running ``CLI_chat.py`` to allow
you to enter test queries.

The steps to run the **librarian** prototype this way are::

1. Copy the ``imagehub_data`` folder that is in the ``test-data`` folder
   to your home directory. The **librarian** requires a populated
   ``imagehub_data`` directory in order to run. Sample data from my own
   **imagehub** directory is in the ``test-data`` folder. You do not have to
   actually run an **imagehub** while running the **librarian**, but that is
   what I do in production. At a minimum, the **librarian** expects an
   ``imagehub_data`` that contains subdirectories ``images`` and ``logs``.
   You can use the sample data provided to run tests.
2. Edit the ``librarian-prototype.yaml`` file and place your edited copy in your
   home directory. You will need to specify the location of your ``imagehub_data``
   directory and a few other options in the yaml file. Comment out the options
   that you don't need in the yaml file using a #, just like a Python comment.
3. Activate your Python virtual environment.
4. Run the **librarian** program in one terminal window:

   .. code-block:: bash

      cd ~/librarian/librarian  # or wherever you folder is
      workon py3cv3
      python librarian.py

5. Then run the CLI_chat.py program to "chat" with the librarian from
   a terminal prompt in a different terminal window:

   .. code-block:: bash

      cd ~/librarian/librarian/helpers/comms  # or wherever your folder is
      workon py3cv3
      python CLI_chat.py

6. You will then enter query words suitable for your imagehub_data events log.
   The Librarian will respond with answers from the events log. Here is an
   example:

   .. code-block::

      (py37cv4) jeffbass@jeff-thinkpad:~/librarian/librarian/helpers/comms$ python CLI_chat.py
      Default Librarian address is: tcp://localhost:5557
      Press enter to keep it, or enter a different one: _?
      CLI Chat with Librarian.
      _? water
      Water is off; last time flowing was at 8:30 PM.
      _? inside temperatures
      Temperature inside house is 75. Temperature in garage is 75.
      _? deck
      Temperature on back deck is 70.
      _? ^C  # press Ctrl-C to exit the program
      (py37cv4) jeffbass@jeff-thinkpad:~/SDBops2/librarian/librarian/helpers/comms$


Running the Librarian Prototype using SMS texting via a Google Voice number
===========================================================================

It is **very** important that you get the **librarian** prototype working with
``CLI_chat.py`` before attempting to use the ``gmail_watcher.py``
program, which watches for incoming SMS text messages sent to a Google Voice
number.

Using the ``gmail_watcher.py`` program requires a thorough knowledge of the
`Gmail Python API <https://developers.google.com/gmail/api/quickstart/python>`_
You will need be familiar with all of the Gmail Python API set up and
credentials creation process for getting it working. If you are not already
familiar with using the Gmail Python API for accessing
Gmail, then you should NOT be using the **librarian** prototype as your
first experiment with using it. If you are familiar with the Gmail API and have
used it successfully in other Python applications, then these steps should be
familiar to you:

1. Set up a Gmail account for use by the **librarian** program. DO NOT use
   the **librarian** Gmail / Google Voice API for an account that is being used
   for anything other than test purposes. Using the Gmail API incorrectly can
   delete all the emails in an account or even cancel the account. Setting up a
   Gmail account is easy and free. Set a new one up for use ONLY by this
   application.
2. Set up a Google Voice number. Use the Gmail account you just created for
   setting up this Google Voice number. As of 2021, Google Voice numbers are
   free, but that could change at any time.
3. Set the Google Voice option to copy SMS messages to Gmail.
4. Set up the Gmail Python API and test it using the Gmail API Python example
   programs. Make sure it is working with your chosen Gmail account. Make sure
   the credential files are created and you can use them correctly.
5. Send an SMS text message to the Google Voice number. Log in to the Gmail
   account and make sure you can read the SMS message. It will appear as an
   email from a phone number in an email address format like
   ``18885551212.18775551212.txt.voice.google.com`` where the first number is
   the Google Voice number receiving the message and the second number is the
   phone number that sent the message.
6. Use the Gmail ``reply`` button to send a short reply to the SMS message.
   Send it. You should see the reply appear on your phone.
7. Edit your librarian.yaml file to "un comment" the gmail settings. They are
   commented out because I don't expect many people to have gotten this far.
8. Edit the ``contacts.txt`` file with the name and phone number of any phone
   that you would want the **librarian** to receive incoming texts from. I often
   have several names and numbers on this "approved texters" list. The format of
   the contacts.txt file is described in the ``get_contacts()`` method of the
   ``gmail.py`` module in the ``comms`` folder. An example ``contacts.txt``
   file appears in each of the a ``gmail`` and a ``gmail2`` directory in the
   ``librarian_data`` folder in the ``test-data`` folder of this repository.
   You will need to edit both of them.
9. You will use ``gmail`` and ``gmail2`` directory in the ``librarian_data``
   directory to hold the Gmail API credentials files for the
   the ``librarian.py`` and ``gmail_watcher.py`` programs, respectively. Some
   "placeholder" credential files are there, but only to show you where they
   wil go once you run your own credentialing process.
10. Make sure there is a copy of your edited ``contacts.txt file`` in each
    of those directories. Yes, it needs to be in both places. Dumb. But I
    haven't fixed it yer.
11. Run the **librarian** program:

    .. code-block:: bash

       cd ~/librarian/librarian
       workon py3cv3
       python librarian.py

    The first time you run this program, a web browser will open for you to
    use your google login to approve the Gmail API, so you must be running on
    a computer that can bring up a web browser when the API credential
    creation process runs.

12. Then run the gmail_watcher.py program to "chat" with the librarian by sending
    SMS text numbers to the Google Voice number you set up:

    .. code-block:: bash

       cd ~/librarian/librarian
       workon py3cv3
       python gmail_watcher.py

    The first time you run this program, a web browser will open for you to
    use you google login to approve the Gmail API, so you must be running on
    a computer that can bring up a web browser when the API credential
    creation process runs.

15. Use a phone to send a text query to the Google Voice number and it will
    send a reply just like the ``CLI_chat.py`` program did.

Setting up the **librarian** prototype for using this Google Voice SMS texting
communications channel is very difficult to debug. You cannot expect to get any
support other than reading the Google Gmail Python API docs and reading the
source code for the **librarian** prototype. It's an experimental prototype.
It works for me. It may or may not work for you and I cannot provide help in
debugging it for you. Frankly, I only included the Google Voice / Gmail
combination in my **librarian** until I could replace it with something better.
It is definitely not easy to set up.

I suggest that you  read the **librarian** prototype code as a model, and then
use a better SMS texting interface such as Twilio rather than the Gmail / Google
Voice technique used in this **librarian** prototype. When a more complete
version of the **librarian** is pushed to its own GitHub repository, it will
include code for using the
`Twilio Python API <https://www.twilio.com/docs/libraries/python>`_
so that a Twilio SMS text number can be used.

Librarian settings via YAML files
=================================

**librarian** requires a *LOT* of settings: settings for **imagehub** data,
settings for the user query communications channels, location of "allowed users"
lists, etc. The settings are put in a YAML file at the home directory level. An
example YAML file is included in the the same directory as the README.rst file.
A description of the ``librarian.yaml`` file and how to adjust its settings
is in `Librarian Settings and YAML files <docs/settings-yaml.rst>`_.

`Return to main documentation page README.rst <../README.rst>`_
