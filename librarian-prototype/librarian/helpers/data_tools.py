"""data_tools: data tools including classes, methods and attributes

Provides a variety of classes to hold, transfer, analyze, transform and query
the various data in the data library and in the imagehubs accessible to the
librarian.

Copyright (c) 2018 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import sys
import pprint
import logging
import threading
import subprocess
from time import sleep
from pathlib import Path
from datetime import datetime
from collections import deque
from helpers.utils import YamlOptionsError

class HubData:
    """ Methods and attributes to transfer data from imagehub data files

    Provides methods for Librarian to access imagehub data, including event
    logs and images stored by the imagehub.

    Parameters:
        settings (Settings object): settings object created from YAML file

    """
    def __init__(self, settings):
        # log directory and log file refer to the event log of the imagehub
        ld = Path(settings.log_directory)
        if not ld.exists():
            raise YamlOptionsError('Log directory in YAML file does not exist.')
        elif not ld.is_dir():
            raise YamlOptionsError('Log directory in YAML file is not a directory.')

        self.log_dir = ld
        self.max_days = 3  # Number of days of hub log files to be loaded
        self.max_history = 300  # Maximum size of the event_deque history
        self.event_data = {}  # see description in load_log_data function
        self.newest_log_line = ''  # keep track of last text line read from log
        self.line_count = 0  # total lines read into event_data since program startup; useful for librarian status
        self.event_data_lock = threading.RLock()

        self.load_log_data(self.log_dir, self.max_days) # inital load self.event_data()
        # pprint.pprint(self.event_data)

        # start thread receive & add data to self.event_data as new lines are
        # added to the imagehub log.
        self.log_check_interval = 2  # seconds: how often check for added log lines
        t = threading.Thread(target=self.watch_for_new_log_lines)
        # print('Starting watch_for_new_log_lines thread.')
        t.daemon = True  # allows this thread to be auto-killed on program exit
        t.name = 'watch_for_new_log_lines'  # naming the thread helps with debugging
        t.start()

        """ # this is the block of lines used to test self.add_new_log_lines()
        print('Total number of lines read from all log files:', self.line_count)
        print('BEFORE call to add_new_log_lines: Newest log line:', self.newest_log_line)
        # testing the add lines modules
        query = input('Add some lines to imagehub.log, then press enter. ')
        self.add_new_log_lines()
        print('AFTER  call to add_new_log_lines: Newest log line:', self.newest_log_line)
        pprint.pprint(self.event_data)
        print('Total number of lines read from all log files:', self.line_count)
        print('End of test')
        sys.exit() """

    def load_log_data(self, ld, max_days):
        """ read the imagehub log file(s), loading the event_deque

        This method reads event lines from the log files. It always reads the
        current log file. It also reads up to "max_days" additional log files.

        Event log files are created by the imagehub.py program. They are created
        using the Python logging module and rotate daily at midnight.

        Event log files are "rotated" using Python's TimedRotatingFileHandler:
        This means the imagehub log files have names like:
            lf.log, lf.log.2020-10-22, lf.log.2020-10-21, lf.log.2020-10-20, ...
        where:
            lf.log is the "current log" that is currently updated by imagehub.
            lf.log.<<date>> is the name pattern for the logs rotated each day.

        The log files are loaded in time order. The oldest log file (up to
        'max_days' old) is loaded. Then the next oldest log file is loaded,
        then the next oldest log file until the current_log file, which is
        always loaded last. The lines from each log file are loaded into the
        event_data deque by the self.load_log_event_lines method.

        Parameters:
          ld (PosixPath): imagehub log directory containing event log files
          max_days (int): number of additional log file day(s) to load

        """

        all_logs = list(ld.glob('*log*'))  # all files that have *log* in them
        current_log = list(ld.glob('*log'))  # current log ends in 'log'
        if not current_log:
            raise YamlOptionsError('There is no file ending in "log".')
        elif len(current_log) > 1:
            raise YamlOptionsError('More than one file ending in "log".')
        else:
            current_log = current_log[0]  # now current log is PosixPath file
        self.log_file = str(current_log)  # string version of log file name
        all_logs.remove(current_log)  # keep only the 'dated' logs
        logs_to_load = list()
        if all_logs:  # we have at least one 'dated' log...
            # ...so get the most recent 'max_days' of them
            all_logs.sort(reverse=True)
            logs_to_load = all_logs[:self.max_days]  # most recent ones
            logs_to_load.sort()  # sort them in time order: oldest to newest
        logs_to_load.append(current_log)  # append the current log last

        for log in logs_to_load:
            with open(log, 'r') as f:
                lines = f.readlines()
            self.load_log_event_lines(lines)

    def load_log_event_lines(self, lines):
        """ loads lines from a log file into the event_data dict()

        Loads event lines from the log files. Loads one line at
        a time, adding the event data to the self.event_data dict() which is a
        nested dictionary. Example data values from self.event_data:

                    node    event         deque of tuples of data values
                     |        |
        event_data['barn']['motion'] values[0] = (datetime, 'moving') # current
                                     values[1] = (datetime, 'moving') # previous
                                     values[2] = (datetime, 'moving') # earlier

        Each data tuple is (datetime, event_value) where each
        event_value is a measure like "77 degrees" or a state like "motion".
        This deque is of fixed length, so as new data points are left_appended,
        those data points beyond max_history are discarded from the event_data
        dictionary (but not from the event log files; those are "read only"
        from the perspective of the librarian; they are written ONLY by the
        imagehub program).

        Parameters:
            lines (list): lines from an imagehub event log file

        """

        for line in lines:
            self.line_count += 1
            # node_tuple is (node, event, when, value)
            node_tuple = self.parse_log_line(line)  # returns "None" if invalid
            if node_tuple:  # only load a valid node_tuple that is not "None"
                self.load_log_event(node_tuple)
        self.newest_log_line = lines[-1]

    def load_log_event(self, node_tuple):
        """ load a single node event into the self.event_data dict()

        Creates a single entry in the self.event_data dict() which holds all
        the recent events logged from imagenodes.

        'node_tuple' objects are parsed from imagehub log lines by the method
        self.parse_log_line(). This method creates entries in self.event_data.

                    node    event         deque of tuples of data values
                     |        |
        event_data['barn']['motion'] values[0] = (datetime, 'moving') # current
                                     values[1] = (datetime, 'moving') # previous
                                     values[2] = (datetime, 'moving') # earlier

        Each data tuple is (datetime, event_value) where each
        event_value is a measure like "77 degrees" or a state like "motion".
        This deque is of fixed length, so as new data points are left_appended,
        those data points beyond max_history are discarded from the event_data
        dictionary (but not from the event log files; those are "read only"
        from the perspective of the librarian; they are written ONLY by the
        imagehub program).

        All string values in the tuple are stripped of whitespace and converted
        to lower case: 'node', 'event', 'value'.

        'when' is a datetime value and is stored as is.

        Parameters:
          node_tuple (tuple): parsed values from a single event log line
        """

        # node_tuple is (node, event, when, value)
        node = node_tuple[0].strip().lower()
        event = node_tuple[1].strip().lower()
        when = node_tuple[2]
        value = node_tuple[3].strip().lower()
        with self.event_data_lock:
            if node not in self.event_data:
                self.event_data[node] = {}
            if event not in self.event_data[node]:
                self.event_data[node][event] = deque(maxlen=self.max_history)
            self.event_data[node][event].appendleft((when, value))

    def parse_log_line(self, line):
        """ parse a single line from a log file returning a tuple of values

        Parses a single event line of text from a log file and returns a tuple
        (node_name, event_type, <<datetime>>, event_value)

        An event_value is a measure like "77 degrees" or a state like "motion".
        This deque is of fixed length, so as new data points are left_appended,
        those data points beyond 'max_history' are discarded from the event_data
        dictionary (but not from the event log files; those are "read only"
        from the perspective of the librarian; they are written ONLY by the
        imagehub program).

        Example:
        Input Log data lines like these:
            2020-06-09 18:27:11,776 ~ Driveway Mailbox|motion|moving
            2020-06-09 18:33:15,788 ~ Barn|Temp|83 F
        Return tuples like these:
            (Driveway Mailbox, motion, <<datetime>>, moving)
            (Barn, Temp, <<datetime>>, 83)

        Parameters:
            line (str): a single log line read from a log file

        Returns:
            tuple (node, event, when, value)
            OR
            None  # if there is not a valid datetime in beginning of line

        """
        two_parts = line.split('~')
        part1 = two_parts[0].strip()
        try:
            when = datetime.strptime(part1, "%Y-%m-%d %H:%M:%S,%f")
        except ValueError:
            return None  # Every valid line has a valid datetime
        part2 = two_parts[1].rstrip(' F\n').strip().split('|')
        if len(part2) < 3:  # this is not a node message; system or other msg
            node = 'non-node'
            event = 'other'
            value = part2[0]  # there will be at least one strng
        else:
            node = part2[0]   # e.g. barn
            event = part2[1]  # e.g. motion
            value = part2[2]  # e.g. still
        return node, event, when, value

    def watch_for_new_log_lines(self):
        """ watch_for_new_log_lines: thread to fetch newly added log lines
        """
        while True:
            self.add_new_log_lines()
            sleep(self.log_check_interval)

    def add_new_log_lines(self):
        """ add new event log data lines to self.event_data dict()

        Runs in a thread that is started when HubData is instantiated.

        Checks imagehub event log file(s) for any changes by using the linux
        "tail" utility (chosen because it is very fast and does NOT read the
        entire file as a Python program would need to). Adds any newly added
        event log lines to the self.event_data dict().

        Algorithm:
        1. tail -n_lines from current log file
        2. is newest_log_line the last line in the tail? return; no new lines
        3. if the tail of n_lines includes the newest_log_line, then
           load_log_event_lines from that line through to the last line in log
        4. else do a tail with more lines up until either find newest_log_line
           or the entire last 2 log files have been returned

        """

        # get n_lines from tail of log file and check if contains last_line_read
        line_num = 0
        try_n_lines = [10, 20, 40, 80, 160, 320, 640, 1024, 2048, 4096]
        for n_lines in try_n_lines:
            # OS command equivalent: tail -n_lines < self.log_file
            lines = self.log_tail(n_lines)
            # print("A: len(lines) is ", len(lines), 'n_lines:', n_lines)
            """ for i, l in enumerate(lines):
                print('Line', i, ':', l)
            print('B: Comparison of lines[-1]:')
            print('B: and self.newest_log_line')
            print(lines[-1][:23])
            print(self.newest_log_line[:23])
            assert lines[-1][:23] == self.newest_log_line[:23], "First 23?"
            assert lines[-1] == self.newest_log_line, "Full length not equal!"
            print('After assert.') """
            # is the last line in the log file still the newest log line?
            if lines[-1][:30] == self.newest_log_line[:30]:
                # print('C: right before return')
                return  # there are no new lines in log file
            # print('D: after lines[-1] comparison:')
            # print('len(lines) vs. n_lines:')
            # print("D: len(lines) is ", len(lines), 'n_lines:', n_lines)
            if len(lines) > n_lines:  # added a 2nd log file, load all lines
                self.load_log_event_lines(lines)
                return
            for n, line in enumerate(lines):  # is newest log line in tail?
                if line[:30] == self.newest_log_line[:30]:  # found a match line
                    # print('About to add lines from', n, ' to ', len(lines)-1 )
                    # for i, l in enumerate(lines[n+1:]):
                        # print('Line', i, ':', l)
                    self.load_log_event_lines(lines[n+1:])
                    return
        return

    def log_tail(self, n_lines):
        """ uses linux "tail" command to get last n_lines from current log file

        Called by add_new_log_lines in a thread that is started when HubData is
        instantiated.

        If n_lines exceeds number of lines in current log file, combine with
        next earlier log file; current limit is 1 earlier log file

        Parameters:
          n_lines (int): number of lines to "tail" from the log file(s).

        Returns:
          lines (list): lines returned by running os command "tail -n_lines"

        """

        n = '-n ' + str(n_lines).strip()  # prepare -n argument
        tail = subprocess.run(['tail', n, self.log_file],
                capture_output=True, text=True)
        lines = tail.stdout.splitlines()  # these lines are from current log file
        if len(lines) < n_lines:  # we got fewer lines than requested;
            # so we add the entire next-oldest log file for testing purposes,
            # and return the lines from both files, first the next-oldtest lines
            # followed by all the lines from the current log file.
            logs = list(self.log_dir.glob('*log*'))  # list of log files
            logs.sort(reverse=True)  # First, sort the entire list reversed
            with open(logs[0], 'r') as f:  # then read the first dated log file
                lines1 = f.readlines()  # which has lines preceding current log file
            lines1.extend(lines)  # both log files are combined; current log is last
            return lines1
        # print('Number of lines returned from log_tail:', len(lines))
        return lines

    def fetch_event_data(self, node, event):
        """ fetch some specified data from event logs or images

        This fetches data from the self.event_data dict() that holds event data.
        Data returned is either 'current' or 'previous', or both, where
        'current' is the  most recent logged event for a node, and 'previous' is
        the one immediately preceding it.

        Returned data values are always a string, even if representing a number.

        Parameters:
          node (str): what node to fetch data for, e.g., barn
          event_type (str): what event or measurement, e.g. temperature or motion

        Returns:
        (2 tuples): (current, previous): with each tuple containing:
          datetime (datetime): the datetime associated with the event
          value (str): the feteched data item, e.g. '77' for temperature
        """

        node = node.strip().lower()  # all string values in event_data are
        event = event.strip().lower()  # already stripped and lower case
        with self.event_data_lock:  # acquire lock to work with event_data updates
            event_type = self.event_data.get(node, None)
            if event_type:
                event_deque = event_type.get(event, None)
                if event_deque:
                    current = event_deque[0]  # the most recent date & value
                    if len(event_deque) > 1:
                        previous = event_deque[1]  # the previous date & value
                    else:
                        previous = None
                    return (current, previous)
                else:
                    return None, " ".join(["Don't know", node, event])
            else:
                return None,  " ".join(["Don't know", node])
