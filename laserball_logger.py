#!/usr/bin/env python
#
# laserball_logger:
#
# LaserballLogger
#
# Simple logging class.
#
# Author: Matt Mottram
#         <m.mottram@sussex.ac.uk>
#
# Adapted for DEAP by: James Waterfield
#                     <jw419@sussex.ac.uk>
#
# History: 2014/05/23 Adapted for DEAP
#
###########################################

import os
import time


def log_message(message, log_file=None, colour=None):
    '''Print a message, log to file as well if possible.
    '''
    curtime = time.strftime("%Y/%m/%d-%H:%M:%S")
    output = curtime + ": " + message
    if log_file is not None:
        curday = time.strftime("_%Y_%m_%d")
        log_file = log_file + curday + '.log'
        f = open(log_file, 'a')
        f.write(output + '\n')
    if colour is not None:
        output = colour + output + '\033[0m'
    print output


class LaserballLogger:
    """A logger, only ever one.
    """

    ## singleton instance
    _instance = None

    class SingletonHelper:

        def __call__(self, *args, **kw):
            if LaserballLogger._instance is None:
                object = LaserballLogger()
                LaserballLogger._instance = object

            return LaserballLogger._instance

    get_instance = SingletonHelper()

    def __init__(self):
        """Should always be called from the __main__ function
        of the master script.
        """
        if not LaserballLogger._instance is None:
            raise Exception("Only one logger allowed")
        LaserballLogger._instance = self
        self._debug_mode = False
        self._log_file = None
        self._colwarn = '\033[91m'
        self._colerr = '\033[41m'
        self._coldbg = '\033[21m'

    def set_debug_mode(self, debug_mode):
        self._debug_mode = debug_mode

    def set_log_file(self, log_file):
        self._log_file = log_file

    def log(self, message):
        log_message(message, self._log_file)

    def debug(self, message):
        if self._debug_mode:
            log_message("DEBUG: " + message, self._log_file, self._coldbg)

    def warn(self, message):
        log_message("WARN: " + message, self._log_file, self._colwarn)
