""" nodehealth: monitor system and network status

    Monitor multiple measures of system and network status, including which
    programs in the yin-yang-ranch system are running. Can be run as a separate
    program from the command line or as part a python program. Intended to be
    run on every computer in the yin-yang-ranch distributed computer vision
    system.

    Copyright (c) 2017 by Jeff Bass.
    License: MIT, see LICENSE for more details.
    """

import sys
import signal
import socket
import logging
import logging.handlers
import platform
from tools.utils import clean_shutdown_when_killed

class HealthMonitor:
    def __init__(self, settings):
        assert sys.version_info >= (3,5)
        self.sys_type = self.get_sys_type()

    def get_sys_type(self):
        uname = platform.uname()
        if uname.system == 'Darwin':
            return 'Mac'
        elif uname.system == 'Linux':
            with open('/etc/os-release') as f:
                osrelease = f.read()
                if 'raspbian' in osrelease.lower():
                    return 'RPi'
                elif 'ubuntu' in osrelease.lower():
                    return 'Ubuntu'
                else:
                    return 'Linux'
        else:
            return 'Unknown'

    def reboot_this_computer(self):
        if self.sys_type == 'RPi':  # reboot only if RPi
            print('This is a mock reboot.')

    def check_ping(self, address='192.168.1.1'):
        return 'OK'  # for testing

def main():
    # set up controlled shutdown when Kill Process or SIGTERM received
    signal.signal(signal.SIGTERM, clean_shutdown_when_killed)

    # start logging
    log = logging.getLogger()
    handler = logging.handlers.RotatingFileHandler('nodehealth.log',
        maxBytes=15000, backupCount=5)
    formatter = logging.Formatter('%(asctime)s ~ %(message)s')
    handler.setFormatter(formatter)
    log.addHandler(handler)
    log.setLevel(logging.DEBUG)

    try:
        log.info('Starting nodehealth.py')
        hostname = socket.gethostname()  # hostname of this computer
        print('This computer is', hostname)
        settings = None
        health = HealthMonitor(settings)
        print('This computer is ', health.sys_type)
        ping_OK = health.check_ping()
        print('Ping Check is ', ping_OK)
        health.reboot_this_computer()
    except (KeyboardInterrupt, SystemExit):
        log.warning('Ctrl-C was pressed or SIGTERM was received.')
    except Exception as ex:
        log.exception('Unanticipated error with no Exception handler.')
        print('Traceback error:', ex)
    finally:
        log.info('Exited nodehealth.py')
        sys.exit()

if __name__ == '__main__' :
    main()
