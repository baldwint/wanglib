#!/usr/bin/env python

"""
Interfaces to motion controllers.

Newport motion cotroller command syntax has significant
overlap between models, so I've written several classes
to keep things as modular as possible.

To control a stage attached to a Newport ESP300 controller,
which is on address 9 of a GPIB network run by a prologix
controller 'plx', you might do this:

>>> from wanglib.instruments.stages import ESP300_stage
>>> esp = instrument(plx, 9)
>>> example_stage = ESP300_stage(1, esp)

Here the 'esp' object is the prologix GPIB connection,
but pyVISA instruments should also work. 

To control another axis of the stage, just make another
ESP300_stage instance using the same instrument object.

>>> other_stage = ESP300_stage(2, esp)

This creates another stage on axis 2.

This class also defines handy classes specific to actual
stages that are on the table, and you probably want those.
For example:

>>> from wanglib.instruments.stages import long_stage
>>> from wanglib.instruments.stages import short_stage

Will get two delay stages, with extra properties representing
the delay in picoseconds, etc.

"""

from wanglib.util import Gpib, num, InstrumentError
from time import sleep

class newport_stage(object):
    """
    Base class for newport stage controllers.

    Commands common to the ESP300 and MM3000 are defined
    here.

    """

    gpib_default = None # overwrite with a default gpib addr
                        # when inheriting

    # necessary properties to define when inheriting:
    #     busy
    #     define_home
    # necessary constants to define when inheriting:
    #    _move_to_limit_cmd
    #    _get_abs_pos_cmd 
    #    _set_abs_pos_cmd
    #    _rel_move_cmd
    #    _one_mm

    def __init__(self, axisnum, bus=None):
        self.axis = int(axisnum)
        if self.gpib_default is None:
            return
        elif bus is None:
            self.bus = Gpib(0, self.gpib_default)
        else:
            self.bus = bus

    def cmd(self, string):
        """ Prepend the axis number to a command. """
        return "%d%s" % (self.axis, string)
 
    def wait(self, lag=0.5):
        """
        Stop the python program until motors stop moving.

        optionally, specify a check interval in seconds
        (default: 0.5)

        """
        while self.busy:
            sleep(lag)

    def move(self, delta):
        """ Move the stage (relative move) """
        self.bus.write(self.cmd(self._rel_move_cmd % delta))
        self.wait()

    def move_to_limit(self, direction=-1):
        """
        Move to the hardware limit of the stage.

        By default, finds the negative limit.
        To find the positive limit, provide a positive
        number as the argument.

        """
        cmd = self._move_to_limit_cmd 
        if direction < 0:
            cmd += '-'
        else:
            cmd += '+'
        self.bus.write(self.cmd(cmd))
        self.wait()

    @property
    def pos(self):
        """ Absolute position of the stage """
        resp = self.bus.ask(self.cmd(self._get_abs_pos_cmd))
        return num(resp.rstrip(' COUNTS'))
    @pos.setter
    def pos(self, val):
        self.bus.write(self.cmd(self._set_abs_pos_cmd % val))
        self.wait()

    def find_zero(self):
        """
        Place the zero 1mm from the hardware limit.
        This follows Yan's old labview routine.

        """
        self.on = True
        #move to negative hardware limit
        self.move_to_limit(-1)
        self.move(self._one_mm)
        self.define_home()

class ESP300_stage(newport_stage):
    """
    A single stage controlled by the ESP300.
    
    """

    gpib_default = 9
    _move_to_limit_cmd = 'MT'
    _get_abs_pos_cmd = 'PA?'
    _set_abs_pos_cmd = 'PA%f'
    _rel_move_cmd =  "PR%f"
    _one_mm = 1 # = 1mm in stage units

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

    @property
    def busy(self):
        """ ask whether motion is in progress """
        resp = self.bus.ask(self.cmd("MD?"))
        return not bool(int(resp))

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

    def define_home(self, loc=None):
        """
        Define the origin of this stage
        to be its current position.

        """
        if loc is not None:
            self.bus.write(self.cmd("DH%f" % loc))
        else:
            self.bus.write(self.cmd("DH0"))


class MM3000_stage(newport_stage):

    gpib_default = 8
    _move_to_limit_cmd = 'ML'
    _get_abs_pos_cmd = 'TP'
    _set_abs_pos_cmd = 'PA%d' # MM3000 only supports integers!
    _rel_move_cmd =  "PR%d" # ditto
    _one_mm = 1e4 # = 1mm in stage units

    @property
    def busy(self):
        # request axis-specific status byte
        sb = self.bus.ask(self.cmd("MS"))
        # the last bit of status byte indicates
        # whether or not it is moving
        return bool(ord(sb) % 2)

    def define_home(self):
        """
        Define the origin of this stage
        to be its current position.

        """
        self.bus.write(self.cmd("DH"))


# all the code up until this point is fairly general to 
# the motion controllers. Now for some useful classes which
# are specific to individual delay stages.

class delay_stage(newport_stage):
    """
    Mixin class for stages used primarily to delay pulses.

    Defines one extra feature: the 't' attribute, which 
    is basically the position of the stage in picosecond units.
    
    When mixing in, you need to define two extra parameters:
        stage_length -- length of the stage, in
                        its natural length units.
        c -- speed of light, in natural length units per picosecond.

    Important: make sure to call 'find_zero' on the stage before
    using t to control motion. Otherwise you might run out of range.

    """

    @property
    def t(self):
        """
        Convert stage position in mm to delay in ps

        """
        # speed of light: 0.3 mm/ps
        t = 2 * (self.stage_length - self.pos) / self.c
        return t

    @t.setter
    def t(self, new_val):
        pos = self.stage_length - (self.c * new_val) * 0.5
        self.pos = pos
 

# finally: the actual stages we use

class long_stage(ESP300_stage, delay_stage):
    stage_length = 600 # mm
    c = 0.3 # mm / ps

class short_stage(MM3000_stage, delay_stage):
    mm = 1e4
    stage_length = 100 * mm 
    c = 0.3 * mm #/ ps

       
