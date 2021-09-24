==============================================
Librarian Settings and the librarian.yaml file
==============================================

.. contents::

========
Overview
========

The **librarian** prototype program does it work by:

- Reading event logs from an **imagehubs** data directory
- Responding to user questions about events in the event logs

All the settings needed to run the **librarian** program are kept in a YAML
file. To test the **librarian**
program, the YAML file needs to be edited. There is a ``print_settings``
option in the yaml file to print the settings.There is no error checking of the
settings in the yaml file; many settings errors will cause a Python traceback
error. The Python traceback error will help identify what setting was
problematic. This is a design choice and is preferable to writing lots of
settings checking code (that could never catch everything anyway ;-)

The ``librarian.yaml`` file is expected to be in the home directory::

  ~/librarian.yaml  # on a typical Linux or Mac OS system

Here is an example ``librarian.yaml`` file where options have been specified:

.. code-block:: yaml

  # Settings file librarian.yaml -- example with lots of settings
  ---
  librarian:
    name: Susan
    queuemax: 50
    patience: 10
    log_directory: /home/jeffbass/imagehub_data/logs # see below for alternatives
    log_file: imagehub.log
    data_directory: librarian_data
    print_settings: False
  comm_channels:
    CLI:
      port: 5557
    gmail:
      port: 5559
      contacts: contacts.txt
      mail_check_seconds: 5
  schedules:
      reminders:
        send_sms_phone_calls:  # this can be any reminder name
          days: all  # or name a weekday like Tuesday
          times: ['10:56', '12:56', '14:56', '16:56']  # times must be in quotes
          channel: gmail_sms
          phone: '8055551212'
          message: Call your dad to check on him
        send_sms_change_batteries:
          days: all
          times: ['23:05']  # times must be in quotes
          channel: gmail_sms
          phone: '8055551212'
          message: Swap nighttime rechargeable battery in Driveway Cam!

=============================
YAML file names and locations
=============================

The **librarian** program expects its settings to be in a file named
``librarian.yaml`` in the home directory.

This code repository comes with an ``librarian-prototype.yaml`` folder that examples
for many settings. It is best not to change the example yaml file so that it
can be used as reference file. Copy a the example yaml file to ``librarian.yaml``
in the home directory. Edit that ``~/librarian.yaml`` file to specify the
address of your **imagehub** directory and set other required and optional
settings.

Conventions used for settings
=============================

Settings follow YAML conventions. Most settings are dictionary key value pairs.
For example:

.. code-block:: yaml

  name: Susan  # name of this Librarian program

The example.yaml files shows how the settings are arranged. There is no error
checking of the settings; if a setting is not set to an expected value, then
a Python traceback error will result. This is adequate for debugging issues
with settings (misspelling a setting name, etc.) and saves writing a lot of
deeply nested if statements. You can also specify an option in the node settings
to print the settings; this can be helpful in spotting option misspellings, etc.

=======================================
Categories of Settings in the YAML file
=======================================

There are 3 settings categories at the root level of the yaml file:

.. code-block:: yaml

  librarian:  # specifies librarian node name and operational settings
  comm_channels:  # specifies communication protocols for CLI, SMS, etc.
  schedules:  # specifies optional scheduled events; ususally sending SMS texts

The ``librarian`` and ``communications`` settings groups are
required and a traceback error will be generated if they are not present or are
misspelled.

Each of the other root level settings groups contains additional nested groups
that allow multiple settings. They can also be nested further as needed,
especially when specifying details of complex communications protocols. The
entire yaml file is read into the settings.config dictionary,
when the Settings() class is called. The 4 dictionaries at the root level of
the yaml file are described first below, then the more nested and detailed
settings in the yaml file are described.

librarian: Settings details
===========================

The 1 required ``librarian`` setting is:

.. code-block:: yaml

  name: A descriptive librarian node name (e.g. Susan)

There can potentially be more than one **librarian** program running on the
same network. Specify a unique name.

There is 5 optional ``librarian`` settings:

.. code-block:: yaml

  patience: maximum number of seconds to wait for a reply from imagehub
  queuemax: maximum size of the memory queue for communications messages, etc.
  print_settings: True or False to print the settings from librarian.yaml file
    (default is False)
    (printing settings can be VERY helpful when debugging settings issues)
  log_directory: /home/jeffbass/imagehub_data/logs # see below for alternatives
  log_file: imagehub.log
  data_directory: librarian_data


The ``patience`` setting sets the maximum number of seconds for **librarian**
to wait for a response from an **imagehub**. The ``patience`` setting specifies
how long to wait for a hub response before calling the ``fix_comm_link``
function that will try to correct the issue. If you do not specify an
``patience`` value, the default is 10 seconds.

The ``queuemax`` setting sets the length of the queues used to hold images,
messages, etc. Default is 50; setting it to a larger value will allow more
images to be stored and sent for each event, but will use more memory.

The ``log_directory`` and ``log_file`` specify the locations of the **imagehub**
data that the **librarian** will read to answer queries. The ``log_directory``
is the pathname of the directory and the ``log_file`` is the name of the most
current event log file. There may be additional, older log files appended with
a date. The format of **imagehub** log files is explained in the **imagehub**
`GitHub repository. <https://github.com/jeffbass/imagehub>`_ There is a
collection of **imagehub** data files in the ``test-data`` folder in this
repository.

The ``data_directory`` specifies then name of the directory where the
**librarian** keeps its own data. For the **librarian** prototype, the only
data are in the ``gmail`` and ``gmail2``. These directories contain credentials
and related data to run the Google Voice / Gmail communications channel. There
is an example ``librarian_data`` directory in the ``test-data`` folder in this
directory.

comm_channels: Settings details
===============================

There must be at least 1 comm_channel specified. For testing, you should
start with the ``CLI`` channel which is used by the ``CLI_chat.py`` text query
program. You can delete or comment out the channel you are not using.

.. code-block:: yaml

  comm_channels:
    CLI:
      port: 5557
    gmail:
      port: 5559
      contacts: contacts.txt
      mail_check_seconds: 5

The comm channel ports are the ZMQ port numbers used by the librarian. They
must be different from the ports used for **imagenode** to **imagehub**
communication if an **imagehub** is running on the same computer as the.
And, if you use multiple comm channels (like CLI and Gmail), they must use and
specify different port numbers.

The Gmail communication channel is used by the Google Voice SMS texting system
that I use to query the librarian. As mentioned elsewhere, the Gmail / Google
Voice SMS texting setup is hard to set up and debug. Not for the faint of heart.
But, if you want to try it, you'll need to specify what ZMQ port to use, the
name of the contacts file (containing a list of allowed inbound texting numbers)
and how often you want ``gmail_watcher.py`` to check for new messages.

schedules: Settings details
===========================

Scheduling of things like backups, object detection updates, etc. have their
settings in this part of the ``librarian.yaml`` file. The ``schedules`` section
of the yaml files is  included as an illustration of possible **librarian**
options.

Since the **librarian** has timing threads and SMS texting capability, I set
up a simple "scheduled SMS text reminder" function as another way to use it. It
was put into the **librarian** prototype as a simple test of the use of
schedules. The settings in the example yaml file show how a couple of these
would be specified. Using this feature assumes that the Gmail / Google Voice
capability is working. If it's not, then this schedules section needs to be
deleted from the yaml file.

Other scheduled functions, such as scheduled backups, are not present in the
**librarian** prototype in this repository. I'm using bash and systemd
methods for these now, but hope to include them in future **librarian** versions.

`Return to main documentation page README.rst <../README.rst>`_
