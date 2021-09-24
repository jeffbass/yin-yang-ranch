"""librarian: Librarian and Settings classes.

Contains the Librarian class and the Settings class.  The Librarian class is the
main Librarian class sets up and runs the librarian program. It reads settings
from the librarian.yaml file.

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import os
import cv2
import sys
import yaml
import pprint
import signal
import imutils
import logging
import imagezmq
import itertools
import threading
import numpy as np
from time import sleep
from pathlib import Path
from ast import literal_eval
from imutils.video import VideoStream
from helpers.schedules import Schedule
from helpers.data_tools import HubData
from helpers.utils import YamlOptionsError
from helpers.nodehealth import HealthMonitor
from helpers.comms.communications import CommChannel
from helpers.comms.chatbot import ChatBot, Conversation

log = logging.getLogger(__name__)

class Librarian:
    """ Contains all the attributes and methods of this librarian.

    One Librarian is instantiated during the startup of the librarian.py
    program. It takes the settings loaded from the YAML file and sets all
    the operational parameters, including the communication channels,
    website interaction, relationship to other librarians (if any),
    image analysis funcions, authorized users, etc.

    The Librarian's 2 primary communications methods are next_query() and
    send_reply() which converse with one or more users. Librarian starts
    threads and subprocesses for many of its functions.

    Parameters:
        settings (Settings object): settings object created from YAML file
    """

    def __init__(self, settings):
        self.log = logging.getLogger()
        # check that numpy and OpenCV are OK
        self.tiny_image = np.zeros((3,3), dtype="uint8")  # tiny blank image
        ret_code, jpg_buffer = cv2.imencode(
            ".jpg", self.tiny_image, [int(cv2.IMWRITE_JPEG_QUALITY), 95])

        self.health = HealthMonitor(settings)  # health check (RPi vs Mac etc.)
        if settings.comm_channels:  # need at least one comm channel in yaml file
            self.setup_comm_channels(settings)
        else:
            raise YamlOptionsError('No comm channels specified in YAML file.')
        self.hub_data = HubData(settings) # imgagehub data class
        self.chatbot = ChatBot(data=self.hub_data)  # conversation methods
        gmail = None
        for channel in self.comm_channels:
            if channel.name == 'Gmail':
                gmail = channel.gmail
                # print('Set gmail object.')
        self.schedule = Schedule(settings, gmail)  # start doing scheduled tasks
        if settings.print:
            self.print_details(settings)

    def setup_comm_channels(self, settings):
        """ Create a list of channels from comm_channels section of YAML file

        Each comm_channel listed in the YAML file will specify multiple details
        like which port, ZMQ versus some other messaging protocol, whether to
        run a thread or a subprocess, etc.

        settings.comm_channels is a dictionary from comm_channels section of
        the YAML file.

        Parameters:
            settings (Settings object): settings object created from YAML file
        """
        self.comm_channels = []
        for channel_type, details in settings.comm_channels.items():
            channel = CommChannel(settings, channel_type, details)
            self.comm_channels.append(channel)

    def print_details(self, settings):
        print('Librarian details:')
        print('  Librarian name:', settings.librarian_name)
        print('  System Type:', self.health.sys_type)
        print()

    def compose_reply(self, request):
        reply = self.chatbot.respond_to(request)
        return reply

    def closeall(self, settings):
        """ Close all resources, files and communications channels.

        Parameters:
            settings (Settings object): settings object created from YAML file
        """
        for channel in self.comm_channels:
            channel.close()

class Settings:
    """Load settings from YAML file

    Note that there is currently almost NO error checking for the YAML
    settings file. Therefore, by design, an exception will be raised
    when a required setting is missing or misspelled in the YAML file.
    This stops the program with a Traceback which will indicate which
    setting below caused the error. Reading the Traceback will indicate
    which line below caused the error. Fix the YAML file and rerun the
    program until the YAML settings file is read correctly.

    There is a "print_settings" option that can be set to TRUE to print
    the dictionary that results from reading the YAML file. Note that the
    order of the items in the dictionary will not necessarily be the order
    of the items in the YAML file (this is a property of Python dictionaries).
    """

    def __init__(self):
        userdir = os.path.expanduser("~")
        with open(os.path.join(userdir,"librarian.yaml")) as f:
            self.config = yaml.safe_load(f)
        self.print_node = False
        if 'librarian' in self.config:
            if 'print_settings' in self.config['librarian']:
                if self.config['librarian']['print_settings']:
                    self.print_settings()
                    self.print = True
                else:
                    self.print = False
        else:
            self.print_settings('"librarian" is a required settings section but not present.')
            raise KeyboardInterrupt
        self.schedules = self.config.get('schedules', None)
        if 'name' in self.config['librarian']:
            self.librarian_name = self.config['librarian']['name']
        else:
            self.print_settings('"name" is a required setting in the "librarian" section but not present.')
            raise YamlOptionsError('No "name" section in yaml file.')
        if 'patience' in self.config['librarian']:
            self.patience = self.config['librarian']['patience']
        else:
            self.patience = 10  # default is to wait 10 seconds
        if 'queuemax' in self.config['librarian']:
            self.queuemax = self.config['librarian']['queuemax']
        else:
            self.queuemax = 50
        if 'heartbeat' in self.config['librarian']:
            self.heartbeat = self.config['librarian']['heartbeat']
        else:
            self.heartbeat = 0
        if 'stall_watcher' in self.config['librarian']:
            self.stall_watcher = self.config['librarian']['stall_watcher']
        else:
            self.stall_watcher = False
        if 'send_threading' in self.config['librarian']:
            self.send_threading = self.config['librarian']['send_threading']
        else:
            self.send_threading = False
        # librararian data directory holds, e.g. gmail credentials & contacts.txt
        if 'data_directory' in self.config['librarian']:
            self.data_directory = self.config['librarian']['data_directory']
        else:
            self.data_directory = 'librarian_data'
        lib_dir = Path.home() / Path(self.data_directory)
        if not lib_dir.exists():
            raise YamlOptionsError('Data directory in YAML file does not exist.')
        elif not lib_dir.is_dir():
            raise YamlOptionsError('Data directory in YAML file is not a directory.')
        self.lib_dir = lib_dir
        if 'log_directory' in self.config['librarian']:
            self.log_directory = self.config['librarian']['log_directory']
        else:
            raise YamlOptionsError('No log directory specified in YAML file.')
        if 'log_file' in self.config['librarian']:
            self.log_file = self.config['librarian']['log_file']
        else:
            raise YamlOptionsError('No log file specified in YAML file.')
        if 'comm_channels' in self.config:
            self.comm_channels = self.config['comm_channels']
        else:
            raise YamlOptionsError('No comm channels specified in YAML file.')

    def print_settings(self, title=None):
        """ prints the settings in the yaml file using pprint()
        """
        if title:
            print(title)
        print('Contents of imagenode.yaml:')
        pprint.pprint(self.config)
        print()
