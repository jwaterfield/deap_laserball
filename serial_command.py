#!/usr/bin/env python
#
# serial_command
#
# SerialCommand
#
# Command functions to send to the laserball
# control box
#
# Author: Matt Mottram
#         <m.mottram@sussex.ac.uk>
#
# Adapted for DEAP by: James Waterfield
#                     <jw419@sussex.ac.uk>
# 
# History:
# 2013/03/08: First instance
# 2013/10/21: Added new classes for different chips, pep8
# 2014/05/23: Adapted for DEAP laserball
#
###########################################
###########################################

import serial
import laserball_exception
#import re  Needed for temperature readout only (Not implemented)
import sys
import time
import laserball_logger
import parameters

_max_pulse_height = 16383
_max_pulse_width = 16383
_max_lo = 255.
_max_pulse_delay = 256.020
_min_pulse_delay = 0.1
_max_pulse_number = 65025
_max_pulse_number_upper = 255
_max_pulse_number_lower = 255

_cmd_fire_continuous = "a" #Continuous pulsing
_cmd_fire_series = "g" #Sequence pulsing
_buffer_end_sequence = "K"
_cmd_stop = "@" #STOP!
_cmd_ph_hi = "L" #Pulse height hi
_cmd_ph_lo = "M" #Pulse height lo
_cmd_ph_end = "P" #Pulse height load
_cmd_pw_hi = "Q" #Pulse width hi
_cmd_pw_lo = "R" #Pulse width lo
_cmd_pw_end = "S" #Pulse width load
_cmd_pn_hi = "H" #Pulse number hi
_cmd_pn_lo = "G" #Pulse number lo
_cmd_pd = "u" #Pulse delay
#_cmd_temp_read = "T" not currently implemented


class SerialCommand(object):
    """Serial command object.
    Base class, different chips then inheret from this.
    """

    def __init__(self, port_name=None):
        """Initialise the serial command"""
        if not port_name:
            self._port_name = "/dev/tty.usbserial-FTE3C0PG"
        else:
            self._port_name = port_name
        # This is the same as a sleep, but with the advantage of breaking
        # if enough characters are seen in the buffer.
        self._port_timeout = 0.3
        self._serial = None
        self.logger = laserball_logger.LaserballLogger.get_instance()
        try:
            self._serial = serial.Serial(port=self._port_name, timeout=self._port_timeout)
            self.logger.debug("Serial connection open: %s" % self._serial)
        except serial.SerialException, e:
            raise laserball_exception.LaserballSerialException(e)
        #cache current settings - remove need to re-command where possible
        self._current_pw = [-999]*96
        self._current_ph = [-999]*96
        self._current_pn = None
        self._current_pd = None
        #information on whether the laserball is being fired
        self._firing = 0 #must wait for firing to complete
        self._reading = 0 #once a read command has been sent, dont send again!
        #if a new channel is selected should force setting all new parameters
        #restriction only lifted once a fire command has been called
        self._force_setting = False
        #send a reset, to ensure the RTS is set to false
        self.reset()


    def __del__(self):
        """Deletion function"""
        if self._serial:
            self._serial.close()

    def _check_clear_buffer(self):
        """Many commands expect an empty buffer, fail if they are not!
        """
        buffer_read = self._serial.read(100)
        if buffer_read != "":
            raise laserball_exception.LaserballException("Buffer not clear: %s" % (buffer_read))

    def _send_command(self, command, readout=True, buffer_check=None):
        """Send a command to the serial port.
        Command can be a chr/str (single write) or a list.
        Lists are used for e.g. a high/low bit command where
        the high bit could finish with an endline (i.e. endstream)"""
        self.logger.debug("_send_command:%s" % command)
        if type(command) is str:
            command = [command]
        if type(command) is not list:
            raise laserball_exception.LaserballException("Command is not a list: %s %s" % (command, type(command)))
        try:
            for c in command:
                self._serial.write(c)
        except:
            raise laserball_exception.LaserballException("Lost connection with Laserball control!")
        if not buffer_check: # assume returns same as input
            buffer_check = ''
            for c in command:
                buffer_check += c
        if readout is True:
            # One read command (with default timeout of 0.1s) should be
            # enough to get all the chars from the readout.
            buffer_read = self._serial.read(len(buffer_check))
            if str(buffer_read)!=str(buffer_check):
                self.logger.debug("problem reading buffer, send %s, read %s" % (command, buffer_read))
                #clear anything else that might be in there
                time.sleep(0.1)
                remainder = self._serial.read(100)
                self._serial.write("@") # send a stop
                time.sleep(0.1)
                self._serial.read(100)
                message = "Unexpected buffer output:\nsaw: %s, remainder %s\nexpected: %s" % (buffer_read, remainder, buffer_check)
                self.logger.warn(message)
                raise laserball_exception.LaserballException(message)
            else:
                self.logger.debug("success reading buffer:%s" % buffer_read)
        else:
            self.logger.debug("not a readout command")

    def _send_setting_command(self, command, buffer_check=None, while_fire=False):
        """Send non-firing command.
        All of these should have a clear buffer before being used.  Can set
        while_fire to True to allow a non-fire command to be sent while firing
        (will cause PIN readout to be flushed to buffer).
        """
        self.logger.debug("Send non-firing command")
        if self._firing is True:
            if while_fire is False:
                raise laserball_exception.LaserballException("Cannot run command, in firing mode")
            else:
                #Assume that we CANNOT readout the buffer here!
                self._send_command(command=command, readout=False)
        else:
            self._check_clear_buffer()
            self._send_command(command=command, buffer_check=buffer_check)

    def reset(self):
        """Send a reset command!

        Assumes that the port is open (which it is by default)
        """
        self.logger.debug("Reset!")
        self._serial.setRTS(True)
        # sleep, just in case
        time.sleep(3.0)
        self._serial.setRTS(False)
        # close the port and reopen?
        time.sleep(3.0)

    def fire(self, while_fire=False):
        """Fire laserball, place class into firing mode.
        Can send a fire command while already in fire mode if required."""
        self.logger.debug("Fire!")
        if self._firing is True and while_fire is False:
            raise laserball_exception.LaserballException("Cannot fire, already in firing mode")
        self.check_ready()
        cmd = None
        buffer_check = _cmd_fire_series
        #if the series is less than 0.5 seconds, also check for the end of sequence
        if (self._current_pn * self._current_pd) < 500:
            buffer_check += _buffer_end_sequence
            self._send_command(_cmd_fire_series, buffer_check=buffer_check)
        else:
            self._send_command(_cmd_fire_series, buffer_check=buffer_check)
            self._firing = True #still firing
        self._force_setting = False

    def fire_continuous(self):
        """Fire Laserball in continous mode.
        """
        if self._firing is True:
            raise laserball_exception.LaserballException("Cannot fire, already in firing mode")
        self._send_command(_cmd_fire_continuous, False)
        self._firing = True
        self._force_setting = False

    def read_buffer(self, n=100):
        return self._serial.read(n)

    def stop(self):
        """Stop firing laserball"""
        self.logger.debug("Stop firing!")
        self._send_command(_cmd_stop, False)
        buffer_contents = self._serial.read(100)
        self._firing = False
        return buffer_contents

    def check_ready(self):
        """Check that all settings have been set"""
        not_set = []
        if self._current_pw is None:
            not_set += ["Pulse width"]
        if self._current_ph is None:
            not_set += ["Pulse height"]
        if self._current_pn is None:
            not_set += ["Pulse number"]
        if self._current_pd is None:
            not_set += ["Pulse delay"]
        if not_set != []:
            raise laserball_exception.LaserballException("Undefined options: %s" % (", ".join(opt for opt in not_set)))

    def clear_settings(self):
        """Clear settings all settings"""
        self._current_pw = None
        self._current_ph = None
        self._current_pn = None
        self._current_pd = None

    def set_pulse_height(self, par):
        """Set the pulse height for the laserball"""
        if par == self._current_ph and not self._force_setting:
            pass #same as current setting
        else:
            self.logger.debug("Set pulse height %s %s" % (par, type(par)))
            command, buffer_check = command_pulse_height(par)
            self._send_setting_command(command=command, buffer_check=buffer_check)
            self._current_ph = par

    def set_pulse_width(self, par, while_fire=False):
        """Set the pulse width for the selected channel.
        This is the only setting that can be modified while in firing mode."""
        if par == self._current_pw and not self._force_setting:
            pass #same as current setting
        else:
            self.logger.debug("Set pulse width %s %s" % (par, type(par)))
            command, buffer_check = command_pulse_width(par)
            if while_fire and self._firing:
                self._send_setting_command(command=command, while_fire=while_fire)
            else:
                self._send__setting_command(command=command, buffer_check=buffer_check)
            self._current_pw = par

    def set_pulse_number(self, par):
        """Set the number of pulses to fire (global setting)"""
        if par == self._current_pn and not self._force_setting:
            pass
        else:
            self.logger.debug("Set pulse number %s %s" % (par, type(par)))
            command, buffer_check = command_pulse_number(par)
            self._send_setting_command(command=command, buffer_check=buffer_check)
            self._current_pn = par

    def set_pulse_delay(self, par):
        """Set the delay between pulses (global setting)"""
        if par == self._current_pd and not self._force_setting:
            pass
        else:
            self.logger.debug("Set pulse delay %s %s" % (par, type(par)))
            command, buffer_check = command_pulse_delay(par)
            self._send_setting_command(command=command, buffer_check=buffer_check)
            self._current_pd = par

    ##################################
    #Temperature module not yet implemented
    ##################################
    #def read_temp(self, timeout=1.0):
    #    """Read the temperature"""
    #    self._send_command(command=cmd, readout=False)
    #    pattern = re.compile(r"""[-+]?\d*\.\d+|\d+""")
    #    #wait for a few seconds before reading out
    #    temp = None
    #    start = time.time()
    #    while not temp:
    #        output = self._serial.read(100)
    #        self.logger.debug("Buffer: %s" % output)
    #        temp = pattern.findall(output)
    #        if time.time() - start > timeout:
    #            raise laserball_exception.LaserballException("Temperature read timeout!")
    #    if len(temp)>1:
    #        raise laserball_exception.LaserballException("Bad number of temp readouts: %s %s" % (len(temp), temp))
    #    temp = float(temp[0])
    #    return temp
    #
    ########################################
    # Commands just to check current settings
    def get_pulse_delay(self):
        """Get the pulse delay
        """
        return self._current_pd

    def get_pulse_number(self):
        """Get the pulse delay
        """
        return self._current_pn

##################################################
# Command options and corresponding buffer outputs
#

def command_pulse_height(par):
    """Get the command to set a pulse height"""
    if par > _max_pulse_height or par < 0:
        raise laserball_exception.LaserballException("Invalid pulse height: %s" % par)
    hi = par >> 8
    lo = par & 255
    command = [_cmd_ph_hi+chr(hi)]
    command+= [_cmd_ph_lo+chr(lo)]
    command+= [_cmd_ph_end]
    buffer_check = _cmd_ph_hi + _cmd_ph_lo + _cmd_ph_end
    return command, buffer_check


def command_pulse_width(par):
    """Get the command to set a pulse width"""
    if par > _max_pulse_width or par < 0:
        raise laserball_exception.LaserballException("Invalid pulse width: %s %s %s" % (par, _max_pulse_width, par>_max_pulse_width))
    hi = par >> 8
    lo = par & 255
    command = [_cmd_pw_hi+chr(hi)]
    command+= [_cmd_pw_lo+chr(lo)+_cmd_pw_end]
    buffer_check = _cmd_pw_hi + _cmd_pw_lo + _cmd_pw_end
    return command, buffer_check


def command_pulse_number(par):
    """Get the command to set a pulse number"""
    if par > _max_pulse_number or par < 0:
        raise laser_exception.LaserballException("Invalid pulse number: %s" % (par))
    par = int(par)
    adjusted, actual_par, hi, lo = parameters.pulse_number(par)
    if adjusted is True:
        raise laserball_exception.LaserballException("Invalid pulse number: %s" % (par))
    command = [_cmd_pn_hi+chr(hi)]
    command+= [_cmd_pn_lo+chr(lo)]
    buffer_check = _cmd_pn_hi + _cmd_pn_lo
    return command, buffer_check


def command_pulse_delay(par):
    """Get the command to set a pulse delay"""
    if par > _max_pulse_delay or par < 0:
        raise laserball_exception.LaserballException("Invalid pulse delay: %s" % par)
    ms = int(par)
    us = int((par-ms)*250)
    command = [_cmd_pd+chr(ms)]
    command+= [chr(us)]
    buffer_check = _cmd_pd
    return command, buffer_check
