"""schedules: schedules all scheduled tasks, maintenace and time based requests

Provides a variety of classes to hold scheduled taks, update them and answer
queries about them.

Copyright (c) 2020 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import sys
import pprint
import logging
import schedule
import threading
import subprocess
from time import sleep
from pathlib import Path
from datetime import datetime
from collections import deque
from helpers.comms.gmail import Gmail
from helpers.utils import YamlOptionsError

log = logging.getLogger(__name__)

class Schedule:
    """ Methods and attributes to manage schedules.

    Provides a variety of classes to hold scheduled taks, update them and answer
    queries about them.

    Parameters:
        settings (Settings object): settings object created from YAML file

    """
    def __init__(self, settings, gmail):
        # get schedules dictionary from yaml file
        schedules = settings.schedules
        self.gmail = gmail
        if schedules:  # at least one schedled item in yaml
            schedule_types = self.load_schedule_data(schedules)  # e.g., reminders
            s = self.setup_schedule(schedule_types)
            self.schedule_run(s)  # run a thread that runs scheduled tasks

    def load_schedule_data(self, schedules):
        """ load schedule data from yaml file dictionary
        Parameters
          schedules (dict): schedule items in yaml file
        Returns:
          schedule_options (list): list of all the requested schedule items
        """
        schedule_types = []
        valid_schedule_types = ['backups', 'reminders']
        for s_type in valid_schedule_types:
            sched = schedules.get(s_type, {})
            if sched:  # not empty
                schedule_types.append(sched)
        # print('schedule_types', *schedule_types)
        return schedule_types

    def setup_schedule(self, schedule_types):
        """ load schedule data from yaml file dictionary
        Parameters:
          schedule_types (list): schedule items in yaml file
        """
        for event_type in schedule_types:  # e.g., reminders, backups, etc.
            for _, event_specs in event_type.items():  # events are nested dictionaries from yaml
                if 'message' in event_specs:  # this event action is 'send message'
                    # days = event_specs.get('days', 'all')  # maybe in future?
                    times = event_specs.get('times', [])
                    # times is a list of times in strings, like '10:30'
                    # print('list of times', *times)
                    message = event_specs.get('message', '')
                    # print('message:', message)
                    channel = event_specs.get('channel', '')
                    # print('channel:', channel)
                    phone = event_specs.get('phone', '')
                    # print('phone:', phone)
                    func = self.send_sms
                    args = (phone, message)
                    for t in times:
                        schedule.every().day.at(t).do(self.send_sms, phone, message)
                    # print('A: Number of timed jobs:', len(schedule.jobs))
        return schedule

    def send_sms(self, phone, message):
        """ send an SMS message

        Sends an SMS message using the Gmail SMS interface.

        Parameters
          phone (str): phone number to send SMS message to
          message (str): message to send via SMS
        """
        # print('Sent:', message, 'To:', phone,  ' -- at', datetime.now().isoformat())
        self.gmail.gmail_send_SMS(phone, message)

    def run_backups(self, source, destination):
        # a possible setup of the backup section of schedules is in example3.yaml
        pass

    def schedule_run(self, schedule):
        """ run all scheduled jobs that have been setup in schedule
        Parameters:
          schedule (schedule object): contains all scheduled jobs
        """

        if len(schedule.jobs):  # no need to start thread if no jobs in queue
            t = threading.Thread(target=self.scheduler_thread)
            # print('Starting scheduler thread')
            t.daemon = True  # allows this thread to be auto-killed on program exit
            t.name = 'Scheduler Thread'  # naming the thread helps with debugging
            t.start()

    def scheduler_thread(self):
        while True:
            schedule.run_pending()
            sleep(1)
