"""image_skills: classes to process images, e.g. detect_objects

Classes to process images, including read a water meter, detect objects and
various others.

Copyright (c) 2020 by Jeff Bass.
License: MIT, see LICENSE for more details.
"""

import sys
import logging
import threading
from time import sleep
from collections import deque

class ImageReader:
    """ Methods and attributes to read images

    Parameters:
        directory: directory holding images

    """
    def __init__(self, directory):
        self.image_directory = directory
        self.last_line_read = ''
        pass

    def fetch_images():
        pass

class ImageSkills:
    """ Methods and attributes to process images, e.g. detect_objects

    Parameters:
        event_q (deque): queue for holding newly added imagehub log lines

    """
    def __init__(self, skill):
        self.skill = skill
        pass

    def read_digits():
        pass
