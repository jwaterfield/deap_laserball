#!/usr/bin/env python
#
# laserball_exception:
#
# LaserballException
#
# Exceptions raised by the laserball modules
#
# Author: Matt Mottram
#         <m.mottram@sussex.ac.uk>
#
# Adapted for DEAP by: James Waterfield
#                     <jw419@sussex.ac.uk>
#
# History:
# 2013/03/08: First instance
# 2014/05/23: Adapted for DEAP
#
###########################################
###########################################

class LaserballException(Exception):
    """General exception for the Laserball command modules"""

    def __init__(self, error):
        Exception.__init__(self, error)


class LaserballSerialException(Exception):
    """Exception when communicating with the Serial Port"""

    def __init__(self, error):
        Exception.__init__(self, error)


class ThreadException(Exception):
    """Exception raised specific to threading issues"""

    def __init__(self, error):
        Exception.__init__(self, error)
