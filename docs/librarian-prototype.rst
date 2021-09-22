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
- Receive and reply to SMS text messages to a Google Voice number
- Answer questions about current status (e.g., Is the water flowing?)
- Include information about the previous state ("water is off; last time flowing was 5:03pm").
- Answer questions about sensor readings ("Inside temperature?")

For example, here is a text message exchange with "Susan", my librarian bot:

.. image:: docs/images/text-messaging.png

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

This **librarian** prototype is incomplete and buggy. It is included in this
repository to allow understanding of one possible design by reading the code. It is
not ready for production use (although I have been running a version of it on
my ranch for about 3 years). This code is the basis the **librarian** version
I am currently developing to push to its own GitHub repository when it has
a more complete set of capabilites.

If you do want to experiment with it, here are some hints to help you install
and run it. But it is experimental...so expect issues.

Dependencies and Installation
=============================

The **librarian** prototype has been tested with:

- Python 3.6 and 3.7
- OpenCV 3.3 & 4.0+
- imagezmq 1.1.1
- imagehub 0.1.0

The **librarian** prototype code is in this repository. Get it by
cloning the GitHub repository::

    git clone https://github.com/jeffbass/yin-yang-ranch.git

Once you have cloned **librarian** to a directory on your local machine,
you can run the tests using the instructions below. The instructions assume you
have cloned **librarian** to the user home directory.

Running the Librarian Prototype
===============================

The steps to run the protype:
1. Make sure you have an **imagehub** that has generated an event log and image
   files. The librarian requires a populated "imagehub_data" directory in order
   to run.
2. Edit the librarian.yaml file and place the edited copy at the user home
   directory.
3. Activate your Python virtual environment. Using the same Python virtual
   environment that is running the **imagehub** works for me.
4. 


Librarian settings via YAML files
=================================

**librarian** requires a *LOT* of settings: settings for **imagehub** access,
settings for the user query communications channels, location of "allowed users"
lists, etc. The settings are put in a YAML file at the home directory level. An
example YAML file is included in the the same directory as the README.rst file.
A description of the ``librarian.yaml`` file and how to adjust its settings
is in `Librarian Settings and YAML files <docs/settings-yaml.rst>`_.

`Return to main documentation page README.rst <../README.rst>`_
