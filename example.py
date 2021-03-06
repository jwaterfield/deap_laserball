#!/usr/bin/env python
#
# example.py
#
# Example of how to use serial_command
# to control the laserball driver
#
# Author: James Waterfield
#        <jw419@sussex.ac.uk>
#
# History:
# 2014/05/23: First instance
#
###################################
###################################
import time
import optparse
import serial_command

if __name__=="__main__":
    parser = optparse.OptionParser()
    parser.add_option("-p",dest="port",default=None) #Port address of usb connection /dev/the_port
    (options, args) = parser.parse_args()
    height = 8000 # pulse width 0-16383 (16383 is max)
    width = 0 # pulse width 0-16383 (0 is max)
    delay = 1 # 0 - 256.02 ms
    number = 12000 # number of pulses 0 - 65025

    #setup board
    sc = serial_command.SerialCommand(options.port)
    sc.clear_channel()
    sc.set_pulse_height(height)
    sc.set_pulse_width(width)
    sc.set_pulse_delay(delay)
    sc.set_pulse_number(number)
    #fire sequence
    sc.fire()

    #fire continuously
    #sc.fire_continuous()
    #time.sleep(1)
    #stop firing
    #sc.stop()

