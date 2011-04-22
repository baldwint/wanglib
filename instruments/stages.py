#!/usr/bin/env python

"""
Interfaces to motion controllers

"""

from wanglib.util import Gpib, num
from time import sleep

class ESP300_stage(object):
    """
    A single stage controlled by the ESP300.

    """

    def __init__(self, axisnum, bus=None):
        self.axis = int(axisnum)
        if bus is None:
            self.bus = Gpib(0,9)
        else:
            self.bus = bus

    def cmd(self, string):
        """ Prepend the axis number to a command. """
        return "%d%s" % (self.axis, string)

    @property
    def on(self):
        """ Turn motor on/off. """
        resp = self.bus.ask(self.cmd("MO?"))
        return bool(int(resp))
    @on.setter
    def on(self, val):
        if val:
            self.bus.write(self.cmd("MO"))
        else:
            self.bus.write(self.cmd("MF"))

    def move(self, delta):
        """ Move the stage (relative move) """
        self.bus.write(self.cmd("PR%f" % delta))
        self.wait()

    @property
    def pos(self):
        """ Absolute position of the stage """
        resp = self.bus.ask(self.cmd("PA?"))
        return num(resp)
    @pos.setter
    def pos(self, val):
        self.bus.write(self.cmd("PA%f" % val))
        self.wait()

    @property
    def busy(self):
        """ ask whether motion is in progress """
        resp = self.bus.ask(self.cmd("MD?"))
        return not bool(int(resp))

    def wait(self, lag=0.5):
        """
        Stop the python program until motors stop moving.

        optionally, specify a check interval in seconds
        (default: 0.5)

        """
        while self.busy:
            sleep(lag)

    def wait_for_motors(self, extra_time=None):
        """
        Wait for motor stop.

        This wait ONLY applies to the motion controller,
        NOT the calling program. Python will continue to
        run along, but the motion controller will be non-
        responsive until the motors stop.
        
        You probably don't even want to use this function.

        To wait a little extra, provide a number
        of milliseconds as the argument.
        
        """
        if extra_time is not None:
            self.bus.write(self.cmd("WS"))
        else:
            self.bus.write(self.cmd("WS%f" % extra_time))

    def move_to_limit(self, direction=-1):
        """
        Move to the hardware limit of the stage.

        By default, finds the negative limit.
        To find the positive limit, provide a positive
        number as the argument.

        """
        if direction < 0:
            self.bus.write(self.cmd("MT-"))
        else:
            self.bus.write(self.cmd("MT+"))
        self.wait()

    def define_home(self, loc=None):
        """
        Define the origin of this stage
        to be its current position.

        """
        if loc is not None:
            self.bus.write(self.cmd("DH%f" % loc))
        else:
            self.bus.write(self.cmd("DH0"))

    def find_zero(self):
        """
        yan's routine places the zero 
        one unit from the hardware motion limit

        """
        self.on = True
        #move to negative hardware limit
        self.move_to_limit(-1)
#        self.wait_for_motors(100)
        self.move(1)
#        self.wait_for_motors(100)
        self.define_home()





