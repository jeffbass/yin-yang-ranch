"""librarian: answer questions; analyze and store images and sensor data

Answers questions about currrent and past observations of imagenodes, including
inputs from PiCameras, USB Webcams, temperature sensors, etc.

Gathers image, sensor and event logs from imagehubs. Does analysis such as
object detection and classification on images. Monitors operational status of
imagenodes and imagehubs. Manages multiple modes of communications for queries
and alerts.

Typically run as a service or background process. See README.rst for details.

Copyright (c) 2017 by Jeff Bass.
License: MIT, see LICENSE for more details.

"""
# populate fields for >>>help(librarian)
from .__version__ import __title__, __description__, __url__, __version__
from .__version__ import __author__, __author_email__, __license__
from .__version__ import __copyright__
