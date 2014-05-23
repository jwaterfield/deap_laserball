deap_laserball
==============

The laserball calibration system for DEAP.

An example script to run the driver has been included. To run:
python example.py -p <port-address>

The port address will be located in the /dev/ folder once the control chip has been connected via usb.

serial_command.py communicates with the control chip.

laserball_logger.py is a simple logging class.

laserball_exception.py is a simple exception class.

parameters.py is for checking any parameters such as pulse number.
