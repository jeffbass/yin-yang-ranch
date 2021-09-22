==============================================
Librarian Settings and the librarian.yaml file
==============================================

.. contents::

========
Overview
========

The **librarian** program does it work by:

- Getting images and event logs from one or more **imagehubs**
- Analyzing the images and event logs (for example, finding objects in images)
- Creating its own summary data from those analyses
- Storing its summary data on persistent media like disks or network storage
- Responding to user questions about images and events and farm status

All the settings needed to run the **librarian** program (to locate its
resources, its local and network storage, its question / answer
communication channels, etc.) are kept in a YAML file. To test the **librarian**
program, the YAML file is changed and the program is re-run to iteratively
"tune" the settings and optimize performance. There is a ``print_settings``
option in the yaml file to print the settings. It can be very useful in catching
spelling errors or other errors in settings. There is no error checking of the
settings in the yaml file; many settings errors will cause a Python traceback
error. The Python traceback error will help identify what setting was
problematic. This is a design choice and is preferable to writing lots of
settings checking code (that could never catch everything anyway ;-)

The librarian.yaml file is expected to be in the home directory::

  ~/librarian.yaml  # on a typical Linux or Mac OS system

Here is an example librarian.yaml file where many options have been specified:

.. code-block:: yaml

  # Settings file librarian.yaml -- example with lots of settings
  ---
  librarian:
    name: Susan
    queuemax: 50
    patience: 10
    heartbeat: 10
    print_settings: True
    stall_watcher: False
    send_threading: False
  communications:
    CLI:
      port: 5556
      protocol: zmq
    SMS:
      protocol: polling  # or subscribe or push
      interval: 5  # how often to poll in seconds
      channel: gvoice
  vision:
    WaterMeter:
      method:
      frquency:
    Barn:
      method:
  website:
    url: https://yin-yang-ranch.com/
    data: data-channel-name  # post address for data
  network:  # this section only needed if there are multiple librarian computers
    central_librarian: user@lib-computer  # or "self" if this is the central one

The above example has more options specified than is typical. But it does
show an actual ``~/librarian.yaml`` file that has been successfully used for
testing a librarian program running on a Linux computer talking to an
**imagehub** on another Linux computer.

=============================
YAML file names and locations
=============================

The **librarian** program expects its settings to be in a file named
``librarian.yaml`` in the home directory.

This code repository comes with an ``yaml`` folder that contains multiple examples
for many settings. It is best not to change the example yaml files so that they
can be used as reference files. Copy a suitable yaml file to "librarian.yaml"
in the home directory. Edit that ``~/librarian.yaml`` file to specify the
address of your **imagehub** computer and set other required and optional
settings.

There is a set of yaml files in the ``tests`` folder. When doing the
suggested tests, the appropriate ``test?.yaml`` file  would be copied to
``~/librarian.yaml`` as part of running a test. Once copied, the yaml file
will need to be edited to set up your specific hub address, etc. See the testing
docs for more info.

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

There are 5 settings categories at the root level of the yaml file:

.. code-block:: yaml

  librarian:  # specifies librarian node name and operational settings
  communications:  # specifies communication protocols for CLI, SMS, etc.
  website:  # specifies protocol for communicating events to a website
  network:  # specifies the location of the central librarian (if more than 1)

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

  heartbeat: an integer number of minutes; how often to send a heartbeat
  patience: maximum number of seconds to wait for a reply from imagehub
  stall_watcher: True or False to start a 'stall_watcher' sub-process
    (default is False)
  queuemax: maximum size of the memory queue for communications messages, etc.
  print_settings: True or False to print the settings from librarian.yaml file
    (default is False)
    (printing settings can be VERY helpful when debugging settings issues)

The ``heartbeat`` is an option that is specified by an integer number of
minutes. It can be helpful when ...

The ``patience`` setting sets the maximum number of seconds for **librarian**
to wait for a response from an **imagehub**. The ``patience`` setting specifies
how long to wait for a hub response before calling the ``fix_comm_link``
function that will try to correct the issue. If you do not specify an
``patience`` value, the default is 10 seconds.

If the ``stall_watcher`` setting is set to ``True``, then a sub-process is
started that watches the main process for "slow downs" or "stalls". Setting
this option to ``True`` will start a 2nd process that checks that the
cumulative cpu time of the main process is increasing as it should. If there
has been some sort of "stall", the main process cpu time stops advancing. If
the ``stall_watcher`` option is set to ``True``, the 2nd process will end the
**librarian** program when a "stall" has been detected, so that the systemd
service can restart **librarian**. An example **imagenode.service** file that
provides for restarting (using systemd / systemctl) is in the main directory.
The ``patience`` option (above) sets the number of seconds between "stall"
checks. If no ``patience`` value is provided, the default is 10 seconds. If
this option is set to ``False`` or is not present, there is no separate
stall watching process started.

The ``queuemax`` setting sets the length of the queues used to hold images,
messages, etc. Default is 50; setting it to a larger value will allow more
images to be stored and sent for each event, but will use more memory.

communications: Settings details
================================

Details of how to specify CLI, gmail, SMS, etc. communication protocols.
((Details to be added))

website: Settings details
=========================

Details of how to specify communication protocols for uploading librarian
data to a website.

network: Settings details
=========================

When there is more than one **imagehub** in the overall system, one **librarian**
program will be running on each computer that is running an **imagehub**. The
settings specified in the network

((Details to be added))


`Return to main documentation page README.rst <../README.rst>`_
