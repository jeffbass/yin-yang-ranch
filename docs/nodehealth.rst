==============================================
nodehealth: system health and failure recovery
==============================================

.. contents::

Overview
========

**nodehealth.py** contains a collection of classes that continuously monitor the
operational health of the node computer and take steps to recover from failures.

Examples of health monitoring
=============================

Wifi strength & selection of strongest known wifi hub
Network ping OK
Communications with imagehub via imagezmq OK

Recovery routines
=================

How a node needs to recover from a problem varies, depending on what type of
system the node is running on (e.g. RPi vs Mac).

Recovery options include::
  restarting the ZMQ connection to imagezmq and the imagehub
  resetting wifi or connecting to different wifi node
  restarting the imagenode.py program
  rebooting the node computer

Restarting imagenode.py after rebooting the Rpi
===============================================

There are multiple ways to start programs on the Raspberry Pi (or any other
Linux system). The two most common ones include "chron" jobs and using the
"systemd / systemctl" service system. The systemd method is more complex, but
allows more control concerning when a program such as imagenode.py is started.
Working out the settings and paramaters for a systemd service took some
experimenting, but a setup that works in documented in the "services" folder
of this repository.
