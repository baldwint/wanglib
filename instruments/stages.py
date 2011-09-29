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
    # specific to the stage:
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

        NOTE: sometimes, the ESP300 will time out and give up
        looking for the hardware limit if it takes too long
        to get there. So, try to get reasonably close to the limit
        before using this function.

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

    def define_home(self, loc=None):
        """
        Define the origin of this stage
        to be its current position.

        To define the current position to be some number
        other than zero, provide that number in the loc kwarg.

        """
        if loc is not None:
            self.bus.write(self.cmd("DH%f" % loc))
        else:
            self.bus.write(self.cmd("DH0"))

    # CALIBRATION FUNCTIONS:

    @property
    def encoder_resolution(self):
        """ Get the distance represented by one encoder pulse. """
        resp = self.bus.ask(self.cmd("SU?"))
        return float(resp)
    @encoder_resolution.setter
    def encoder_resolution(self, val):
        """ adjust the encoder calibration. """
        self.bus.write(self.cmd("SU%f" % val))

    @property
    def step_size(self):
        """ Get the distance represented by one motor step. """
        resp = self.bus.ask(self.cmd("FR?"))
        return float(resp)
    @step_size.setter
    def step_size(self, val):
        """ adjust the motor calibration. """
        self.bus.write(self.cmd("FR%f" % val))

    def get_max_velocity(self):
        """ Get the maximum motor velocity. """
        resp = self.bus.ask(self.cmd("VU?"))
        return float(resp)

    def set_max_velocity(self, val):
        """ Set the max motor velocity. """
        self.bus.write(self.cmd("VU%f" % val))

    def get_velocity(self):
        """ Get the current motor velocity. """
        resp = self.bus.ask(self.cmd("VA?"))
        return float(resp)

    def set_velocity(self, val):
        """ Set the motor velocity. """
        self.bus.write(self.cmd("VA%f" % val))

    # UNIT LABELS:

    _unit_labels = {
        0: 'counts',
        1: 'steps',
        2: 'mm',
        3: 'um',
    }

    @property
    def unit(self):
        """ Get the unit label for a given axis. """
        resp = self.bus.ask(self.cmd("SN?"))
        return self._unit_labels[int(resp)]

    def set_unit(self, key):
        """
        Set the unit label for a given axis, by index.

        Unit labels ('mm', 'um', etc) have corresponding
        integer indices. Look these up in the _unit_labels
        dictionary.

        """
        #TODO: reverse dictionary lookup would be nice
        key = int(key)
        resp = self.bus.ask(self.cmd("SN%d" % key))


class MM3000_stage(newport_stage):
    """
    A Newport MM3000 motion controller.
    
    """

    gpib_default = 8
    _move_to_limit_cmd = 'ML'
    _get_abs_pos_cmd = 'TP'
    _set_abs_pos_cmd = 'PA%d' # MM3000 only supports integers!
    _rel_move_cmd =  "PR%d" # ditto

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
 

# finally: the actual stages we use on the table

class thorlabs_Z612B(ESP300_stage):
    """ Thorlabs Z612B motorized actuator. """

    _one_mm = 1000

    def initialize(self):
        um = 3 # index for 'um' label
        self.set_unit(um)

        # thread pitch: 0.5 mm
        # gear reduction: 256 : 1
        self.step_size = 500./256
        
        # encoder: 48 ticks/rev at motor
        # this theoretically makes for 40nm resolution
        self.encoder_resolution = self.step_size / 48

        # max velocity 425 um/sec
        self.set_max_velocity(425)
        self.set_velocity(200)

class long_stage(ESP300_stage, delay_stage):
    _one_mm = 1 # = 1mm in stage units
    stage_length = 600 # mm
    c = 0.3 # mm / ps

class short_stage(MM3000_stage, delay_stage):
    _one_mm = 1e4 # = 1mm in stage units
    mm = 1e4
    stage_length = 100 * mm 
    c = 0.3 * mm #/ ps

       
