#######################
# parameters.py:
#  Any parameters that may need checking
#
# Author: James Waterfield
#        <jw419@sussex.ac.uk>
#
#######################
#######################
import math

max_pulse_number = 65025

def pulse_number(number):
    adjusted = False
    if type(number)!=int:
        raise Exception("PN must be an integer")
    if number > max_pulse_number:
        raise Exception("PN must be < %d.  You set %d" % (65025, number))
        #number = max_pulse_number
        #adjusted = True
    hi = -1
    lo = -1
    diff = 100000 # bigger than max pn
    for i in range(1, 256):
        #assume hi is i
        lo_check = number/i
        if lo_check > 255:
            lo_check = 255
        check = i * lo_check
        if math.fabs(check - number) < diff:
            diff = math.fabs(check - number)
            hi = i
            lo = lo_check
        if check == number:
            break
    actual_par = hi * lo
    if actual_par != number:
        adjusted = True
    return adjusted, actual_par, hi, lo
