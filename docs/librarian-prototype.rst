=======================================================================
A simple prototype of the Librarian and related Communications Programs
=======================================================================

Introduction
============

The **librarian** is the program at the heart of the yin-yang-ranch system. It acts
as a librarian would be expected to. It keeps track of lots of information that
is on file, and answers questions about it. It also creates summary files, does
backups and checks that all the other systems are working OK. Most of the
information that the **librarian** keeps track of is the data sent by
**imagenodes** to **imagehubs**, including images, sensor readings and event
messages There are also some included programs to monitor **imagenode** heatlh.

.. contents::

Overview
========

The **librarian** prototype has limited functionality. It can:

- Receive and reply to queries from a simple terminal CLI interface
- Receive and reply to SMS text messages using a Google Voice number
- Answer questions about current status (e.g., Is the water flowing?)
- Include information about a previous state ("water is off; last time flowing was 5:03pm").
- Answer questions about sensor readings ("Inside temperature?")

For example, here is a text message exchange with "Susan", my librarian bot:

.. image:: docs/images/text-messaging.png

That is a screen shot from a phone that had texted the Google Voice phone
number that is watched by the **librarian** prototype. The **librarian** code
that is in this repository was running when the screen shot was generated.

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
of how to set up "scheduled SMS text messages" in the ```librarian.yaml`` file.

This **librarian** prototype is incomplete and buggy. It is included in this
repository to convey understanding of one possible design. It is
not ready for production use (although I have been running a version of it on
my ranch for about 3 years). This code is the basis for the **librarian** version
I am currently developing to push to its own GitHub repository when it has
a more complete and reliable set of capabilites.

If you do want to experiment with it, here are some hints to help you install
and run it. But please remember that it is experimental...so expect issues.

Dependencies and Installation
=============================

The **librarian** prototype has been tested with:

- Python 3.6 and 3.7
- OpenCV 3.3 & 4.0+
- imagezmq 1.1.1
- imagehub 0.1.0

The **librarian** prototype code is in this repository. Get it by
cloning this GitHub repository::

    git clone https://github.com/jeffbass/yin-yang-ranch.git

Once you have cloned **librarian** to a directory on your local machine,
you can run some tests using the instructions below.

Running the Librarian Prototype
===============================

The steps to run the prototype:
1. Make sure you have an **imagehub** that has generated an event log and image
   files. The librarian requires a populated "imagehub_data" directory in order
   to run. A sample event log is in the examples directory. You do not have to
   actually run the **imagehub** while running the **librarian**, but that is
   what I do in production. At a minimum, the **librarian** expects an
   ``imagehub_data`` that contains subdirectories ``images`` and ``logs``.
   There is an ``example_image_data`` folder in this repository.
2. Edit the librarian.yaml file and place your edited copy in your user home
   directory. You will need to specify the location of your ``imagehub_data``
   directory and a few other options in the yaml file. Comment out the options
   that you don't need in the yaml file using a #, just like a Python comment.
3. Activate your Python virtual environment.
4. Run the **librarian** program:

   .. code-block:: bash

    cd ~/librarian/librarian
    workon py3cv3
    python librarian.py

5. Then run the CLI_chat.py program to "chat" with the librarian from
   a terminal prompt:

   .. code-block:: bash
     cd ~/librarian/librarian/helpers/comms
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


It is important that you get the **librarian** prototype working with
``CLI_chat.py`` before attempting to use the ``gmail_watcher.py``
program, which watches for incoming SMS text messages sent to a Google Voice
number.

Using the ``gmail_watcher.py`` program requires a thorough knowledge of the Gmail
Python API and all of the set up and credentials creation process for getting it working.
If you are not already familiar with using the Gmail Python API for accessing
Gmail, then you should NOT be using the **librarian** prototype as your
first experiment with using it. If you are familiar with the Gmail API and have used
it successfully in other Python applications, then these steps should be familiar
to you:
1. Set up a Gmail account for use by the **librarian** program. DO NOT use
   the **librarian** Gmail / Google Voice API for an account that is being used
   for anything other than test purposes. Using the Gmail API incorrectly can
   delete all the emails in an account or even cancel the account. Setting up a
   Gmail account is easy and free. Set one up for use only by this application.
2. Set up a Google Voice number. Use the Gmail account you just created for
   setting up this Google Voice number. As of 2021, Google Voice numbers are
   free, but that could change at any time.
3. Set the Google Voice option to copy SMS messages to Gmail.
4. Set up the Gmail Python API and test it using the Gmail API Python example
   programs. Make sure it is working with your chosen Gmail account. Make sure
   the credential files are created and you can use them correctly.
5. Send an SMS text message to the Google Voice number. Log in to the Gmail
   account and make sure you can read the SMS message. It will appear as an
   email from a phone number in a format like
   ``18885551212.18775551212.txt.voice.google.com`` where the first number is
   the receiving Google Voice number and the second number is the phone that
   sent the message.
6. Use the Gmail ``reply`` button to send a short reply to the SMS message.
   Sent it. You should see the reply appear on your phone.
7. Edit your librarian.yaml file to "un comment" the gmail settings.
8. Create a ``contacts.txt`` file with the name and phone number of any phone
   that you would want the **librarian** to take incoming texts from. I often
   have several names and numbers on this "approved texters" list. The format of
   the contacts.txt file is described in the ``get_contacts()`` method of the
   ``gmail.py`` module in the ``comms`` folder.
9. Create a ``gmail`` and a ``gmail2`` directory in the ``librarian_data``
   directory. These 2 directories hold the credentials files for the
   the ``librarian.py`` and ``gmail_watcher.py`` programs, respectively.
10. Put a copy of your contacts.txt file in each of those directories. Yes, it
    needs to be in both places.
11. Move your Gmail API credentials to each of these directories as well.
12. Run the **librarian** program:

    .. code-block:: bash
       cd ~/librarian/librarian
       workon py3cv3
       python librarian.py

    The first time you run this program, a web browser will open for you to
    use your google login to approve the Gmail API, so you must be running on
    a computer that can bring up a web browser when the API credential
    creation process runs.

13. Then run the gmail_watcher.py program to "chat" with the librarian by sending
    SMS text numbers to the Google Voice number you set up:

    .. code-block:: bash
       cd ~/librarian/librarian
       workon py3cv3
       python gmail_watcher.py

    The first time you run this program, a web browser will open for you to
    use you google login to approve the Gmail API, so you must be running on
    a computer that can bring up a web browser when the API credential
    creation process runs.

14. Use a phone to send a text query to the Google Voice number and it will
    send a reply just like the ``CLI_chat.py`` program did.

Setting up the **librarian** prototype for using this Google Voice SMS texting
communications channel is difficult to debug. You cannot expect to get any
support other than reading the Google Gmail Python API docs and reading the
source code for the **librarian** prototype. It's an experimental prototype.
It works for me. It may or may not work for you and I cannot provide help in
debugging it for you.

You may want to read the **librarian** prototype code as a model, and then use
a different SMS texting interface such as Twilio rather than the Gmail / Google
Voice technique used in this **librarian** prototype.

Librarian settings via YAML files
=================================

**librarian** requires a *LOT* of settings: settings for **imagehub** data,
settings for the user query communications channels, location of "allowed users"
lists, etc. The settings are put in a YAML file at the home directory level. An
example YAML file is included in the the same directory as the README.rst file.
A description of the ``librarian.yaml`` file and how to adjust its settings
is in `Librarian Settings and YAML files <docs/settings-yaml.rst>`_.

`Return to main documentation page README.rst <../README.rst>`_
