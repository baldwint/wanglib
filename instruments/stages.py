#!/usr/bin/env python

"""
Interfaces to motion controllers.

Newport motion cotroller command syntax has significant
overlap between models, so I've written several classes
to keep things as modular as possible.

Only two of the classes defined here represent actual
stages that are on the table, and you probably want those.
For example:

>>> from wanglib.instruments.stages import long_stage
>>> from wanglib.instruments.stages import short_stage

These stages are controlled by stage controllers. Make sure
to also import the stage controller that you'll need.

>>> from wanglib.instruments.stages import ESP300
>>> from wanglib.instruments.stages import MM3000

Most stages only work with certain controllers. Set up the 
long stage like so:

>>> esp = ESP300(plx, 9)
>>> sg = long_stage(esp, 1)

Here plx is the gpib controller, and 9 is the gpib address
of the newport ESP300. The ESP300 can have 3 stages (axes)
attached to it. The long stage happens to be on axis 1.

For a short stage, we have to use the old motion controller.
Set that up like

>>> sw = short_stage(MM3000(plx, 8), 2)

This instantiates the short stage on axis 2 of the MM3000.
The MM3000 is on the same GPIB network, at address 8.

Notice that I did it all on one line. Since I won't need
that MM3000 controller for any other purpose, I don't bother
keeping a reference as I did in the previous example ("esp").

"""

from wanglib.util import Gpib, num, InstrumentError
from time import sleep

class newport_stage_controller(object):
    """
    Base class for newport stage controllers.

    Commands common to the ESP300 and MM3000 are defined
    here.

    """

    gpib_default = None # overwrite with a default gpib addr
                        # when inheriting

    # necessary functions to define when inheriting:
    #     is_axis_busy 
    #     define_axis_home
    # necessary constants to define when inheriting:
    #    _move_to_limit_cmd
    #    _get_abs_pos_cmd 
    #    _set_abs_pos_cmd
    #    _rel_move_cmd

    def __init__(self, bus=None):
        if self.gpib_default is None:
            return
        elif bus is None:
            self.bus = Gpib(0, self.gpib_default)
        else:
            self.bus = bus

    def cmd(self, string, axis): 
        """ Prepend the axis number to a command. """
        return "%d%s" % (axis, string)
 
    def wait(self, axis, lag=0.5):
        """
        Stop the python program until a given axis stops moving.

        optionally, specify a check interval in seconds
        (default: 0.5)

        """
        while self.is_axis_busy(axis):
            sleep(lag)

    def move_axis(self, axis, delta): 
        """ Move a given axis (relative move) """
        self.bus.write(self.cmd(self._rel_move_cmd % delta, axis))
        self.wait(axis)

    def move_axis_to_limit(self, axis, direction=-1): 
        """
        Move a given axis to the hardware limit.

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
        self.bus.write(self.cmd(cmd, axis))
        self.wait(axis)

    def get_axis_position(self, axis): 
        """ Absolute position of the stage """
        resp = self.bus.ask(self.cmd(self._get_abs_pos_cmd, axis))
        return num(resp.rstrip(' COUNTS'))
    def set_axis_position(self, axis, val):
        self.bus.write(self.cmd(self._set_abs_pos_cmd % val, axis))
        self.wait(axis)

class ESP300(newport_stage_controller):
    """
    A Newport ESP300 motion controller.
    
    """

    gpib_default = 9
    _move_to_limit_cmd = 'MT'
    _get_abs_pos_cmd = 'PA?'
    _set_abs_pos_cmd = 'PA%f'
    _rel_move_cmd =  "PR%f"

    def is_axis_on(self, axis):
        """ ask whether a given axis is on or off """
        resp = self.bus.ask(self.cmd("MO?", axis))
        return bool(int(resp))

    def turn_axis_on(self, axis):
        self.bus.write(self.cmd("MO", axis))
    def turn_axis_off(self, axis):
        self.bus.write(self.cmd("MF", axis))

    def is_axis_busy(self, axis):
        """ ask whether motion is in progress """
        resp = self.bus.ask(self.cmd("MD?", axis))
        return not bool(int(resp))

    def define_axis_home(self, axis, loc=None):
        """
        Define the origin of this stage
        to be its current position.

        To define the current position to be some number
        other than zero, provide that number in the loc kwarg.

        """
        if loc is not None:
            self.bus.write(self.cmd("DH%f" % loc, axis))
        else:
            self.bus.write(self.cmd("DH0", axis))

    # CALIBRATION FUNCTIONS:

    def get_axis_encoder_resolution(self, axis):
        """ Get the distance represented by one encoder pulse. """
        resp = self.bus.ask(self.cmd("SU?", axis))
        return float(resp)

    def set_axis_encoder_resolution(self, axis, val):
        """ adjust the encoder calibration. """
        self.bus.write(self.cmd("SU%f" % val, axis))

    def get_axis_step_size(self, axis):
        """ Get the distance represented by one motor step. """
        resp = self.bus.ask(self.cmd("FR?", axis))
        return float(resp)

    def set_axis_step_size(self, axis, val):
        """ adjust the motor calibration. """
        self.bus.write(self.cmd("FR%f" % val, axis))

    def get_axis_max_velocity(self, axis):
        """ Get the maximum motor velocity. """
        resp = self.bus.ask(self.cmd("VU?", axis))
        return float(resp)

    def set_axis_max_velocity(self, axis, val):
        """ Set the max motor velocity. """
        self.bus.write(self.cmd("VU%f" % val, axis))

    def get_axis_velocity(self, axis):
        """ Get the current motor velocity. """
        resp = self.bus.ask(self.cmd("VA?", axis))
        return float(resp)

    def set_axis_velocity(self, axis, val):
        """ Set the motor velocity. """
        self.bus.write(self.cmd("VA%f" % val, axis))

    # UNIT LABELS:

    _unit_labels = {
        0: 'counts',
        1: 'steps',
        2: 'mm',
        3: 'um',
    }

    def get_axis_unit_label(self, axis):
        """ Get the unit label for a given axis. """
        resp = self.bus.ask(self.cmd("SN?", axis))
        return self._unit_labels[int(resp)]

    def set_axis_unit_label(self, axis, key):
        """
        Set the unit label for a given axis.

        Use the index in the dictionary above.

        """
        key = int(key)
        resp = self.bus.ask(self.cmd("SN%d" % key, axis))


class MM3000(newport_stage_controller):
    """
    A Newport MM3000 motion controller.
    
    """

    gpib_default = 8
    _move_to_limit_cmd = 'ML'
    _get_abs_pos_cmd = 'TP'
    _set_abs_pos_cmd = 'PA%d' # MM3000 only supports integers!
    _rel_move_cmd =  "PR%d" # ditto

    def is_axis_busy(self, axis):
        """ ask whether motion is in progress """
        # request axis-specific status byte
        sb = self.bus.ask(self.cmd("MS", axis))
        # the last bit of status byte indicates
        # whether or not it is moving
        return bool(ord(sb) % 2)

    def define_axis_home(self, axis):
        """
        Define the origin of this stage
        to be its current position.

        """
        self.bus.write(self.cmd("DH", axis))



# all code up to this point tells us how to talk to motion controllers.
# now for some useful classes that represent the stages themselves.

class stage(object):
    """
    base class for a generic, individual stage. 

    motions of this stage are controlled by interfacing
    with an external controller object.

    """
    # necessary constants to define when inheriting:
    #    _one_mm

    def __init__(self, controller, axis):
        """
        When instantiating, provide the axis number
        and the controller object (MM3000 or ESP300 instance)
        which this stage is hooked up to.

        For example, for a stage hooked up to the ESP300 on axis 1, do

        >>> esp = ESP300() # instantiate as necessary
        >>> sg = stage(esp, 1)

        """
        self.axis = axis
        self.controller = controller

#        if not hasattr(self.controller, 'is_axis_on'):
#            # define on/off switch only if our controller
#            # supports it (MM3000 doesn't)
#            print self["on"]

    @property
    def busy(self):
        return self.controller.is_axis_busy(self.axis)

    # use this property to move the stage around.
    @property
    def pos(self): 
        return self.controller.get_axis_position(self.axis)
    @pos.setter
    def pos(self, val):
        self.controller.set_axis_position(self.axis, val)

    def move(self, delta): 
        """ Move the stage (relative move) """
        self.controller.move_axis(self.axis, delta)

    def move_to_limit(self, direction=-1): 
        """
        Move to the hardware limit of the stage.

        By default, finds the negative limit.
        To find the positive limit, provide a positive
        number as the argument.

        """
        self.controller.move_axis_to_limit(self.axis, direction)
 
    def find_zero(self): 
        """
        Place the zero 1mm from the hardware limit.
        This follows Yan's old labview routine.

        """
        try:
            self.on = True
        except AttributeError: # the stage controller doesn't support
            pass                # turning stages on/off
        #move to negative hardware limit
        self.move_to_limit(-1)
        self.move(self._one_mm)
        self.controller.define_axis_home(self.axis)

    # the on/off property will only work if the controller
    # supports it (MM3000 doesn't, those stages are always on)
    @property
    def on(self):
        return self.controller.is_axis_on(self.axis)
    @on.setter
    def on(self, val):
        if val:
            self.controller.turn_axis_on(self.axis)
        else:
            self.controller.turn_axis_off(self.axis)

    # these properties will only work with ESP300
    # TODO: programmatically create properties based on
    # matching to controller.get_axis_.* methods
    @property
    def step_size(self):
        return self.controller.get_axis_step_size(self.axis)
    @step_size.setter
    def step_size(self, val):
        return self.controller.set_axis_step_size(self.axis, val)

    @property
    def encoder_resolution(self):
        return self.controller.get_axis_encoder_resolution(self.axis)
    @encoder_resolution.setter
    def encoder_resolution(self, val):
        return self.controller.set_axis_encoder_resolution(self.axis, val)

    @property
    def unit(self):
        return self.controller.get_axis_unit_label(self.axis)


class delay_stage(object):
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

class thorlabs_Z612B(stage):
    """ Thorlabs Z612B motorized actuator. """

    _one_mm = 1000

    def initialize(self):
        um = 3 # index for 'um' label
        self.controller.set_axis_unit_label(self.axis, um)

        # thread pitch: 0.5 mm
        # gear reduction: 256 : 1
        self.step_size = 500./256
        
        # encoder: 48 ticks/rev at motor
        # this theoretically makes for 40mm resolution
        self.encoder_resolution = self.step_size / 48

        # max velocity 425 um/sec
        self.controller.set_axis_max_velocity(self.axis, 425)
        self.controller.set_axis_velocity(self.axis, 200)

class long_stage(stage, delay_stage):
    _one_mm = 1 # = 1mm in stage units
    stage_length = 600 # mm
    c = 0.3 # mm / ps

class short_stage(stage, delay_stage):
    _one_mm = 1e4 # = 1mm in stage units
    mm = 1e4
    stage_length = 100 * mm 
    c = 0.3 * mm #/ ps

       
