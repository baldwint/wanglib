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
>>> esp = plx.instrument(9)
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

from wanglib.util import num, InstrumentError, Serial
from time import sleep

class _newport_stage(object):
    """
    Base class for newport stage controllers.

    Don't instantiate it!

    Commands common to the ESP300 and MM3000 are defined
    here.

    """

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

    def get_pos(self):
        """ Query the absolute position of the stage """
        resp = self.bus.ask(self.cmd(self._get_abs_pos_cmd))
        return num(resp.rstrip(' COUNTS'))
    def set_pos(self, val):
        """ Set the absolute position of the stage """
        self.bus.write(self.cmd(self._set_abs_pos_cmd % val))
        self.wait()
    pos = property(get_pos, set_pos)
    """ Absolute position of the stage """

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

class ESP300_stage(_newport_stage):
    r"""
    A single stage controlled by the ESP300.

    The ESP300 is typically on GPIB address 9.

    To use over RS232, use the following parameters:
        :baudrate: 19200
        :rtscts:   True
        :term_chars: ``\r\n``

    These settings are used by default if you simply pass
    the name of the serial port as a string:

    >>> my_stage = ESP300_stage(1, '/dev/ttyUSB')

    This will make an object corresponding to axis 1 of the stage.

    For full control over the RS232 communication, provide a
    ``Serial`` instance instead of an address. For example:

    >>> from wanglib.util import Serial
    >>> esp = Serial('/dev/ttyUSB', baudrate=19200, timeout=10, 
    ...             rtscts=1, log='esp300.log', term_chars="\r\n")
    >>> my_stage = ESP300_stage(1, esp)

    This will work the same as above, but also log command
    traffic to the file ``esp300.log``.
    
    """

    _move_to_limit_cmd = 'MT'
    _get_abs_pos_cmd = 'PA?'
    _set_abs_pos_cmd = 'PA%f'
    _rel_move_cmd =  "PR%f"

    def __init__(self, axisnum, bus=None):
        if type(bus) is str:
            # if only a device name is given, create a serial instance
            bus = Serial(bus, baudrate=19200,
                         timeout=10, rtscts=1,
                         term_chars="\r\n")
        super(ESP300_stage, self).__init__(axisnum, bus)

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
        self.bus.write(self.cmd("SN%d" % key))


class MM3000_stage(_newport_stage):
    """
    A single stage controlled by the Newport MM3000 motion controller.

    Firmware version: 2.2

    The MM3000 is typically on GPIB address 8.
    
    """

    _move_to_limit_cmd = 'ML'
    _get_abs_pos_cmd = 'TP'
    _set_abs_pos_cmd = 'PA%d' # MM3000 only supports integers!
    _rel_move_cmd =  "PR%d" # ditto

    def motor_status(self, bit=None):
        """
        Request the MM3000 motor status byte.
        
        Optionally, pick out a specific bit.
            bit 0: True if axis is moving
            bit 1: True if motor is *off*
            bit 2: True if direction of move is positive
            bit 3: True if positive travel limit is active
            bit 4: True if negative travel limit is active
            bit 5: True if positive side of home
            bit 6: always True
            bit 7: always False

        """
        sb = self.bus.ask(self.cmd("MS"))
        if bit is None:
            return sb
        else:
            # bit shift right, return last bit
            return bool((ord(sb) >> int(bit)) % 2)

    @property
    def busy(self):
        # the last bit of status byte indicates
        # whether or not it is moving
        return self.motor_status(0)

    @property
    def on(self):
        return not self.motor_status(1)
    @on.setter
    def on(self, val):
        if val:
            self.bus.write(self.cmd("MO"))
        else:
            self.bus.write(self.cmd("MF"))


    def define_home(self):
        """
        Define the origin of this stage
        to be its current position.

        """
        self.bus.write(self.cmd("DH"))


# all the code up until this point is fairly general to 
# the motion controllers. Now for some useful classes which
# are specific to individual delay stages.

class delay_stage(_newport_stage):
    """
    Mixin class for stages used primarily to delay pulses.

    Defines one extra feature: the 't' attribute, which 
    is basically the position of the stage in picosecond units.
    
    When mixing in, you need to define two extra attributes:
        :stage_length: length of the stage, in
                       its natural length units.
        :c: speed of light, in natural length units per picosecond.

    Important: make sure to call 'find_zero' on the stage before
    using t to control motion. Otherwise you might run out of range.

    """

    def get_t(self):
        """
        Convert stage position in mm to delay in ps

        """
        # speed of light: 0.3 mm/ps
        t = 2 * (self.stage_length - self.pos) / self.c
        return t

    def set_t(self, new_val):
        pos = self.stage_length - (self.c * new_val) * 0.5
        self.pos = pos

    t = property(get_t, set_t)
 

# finally: the actual stages we use on the table

# TODO: make these classes independent of the
# controller they're plugged into

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

class shorty_stage(ESP300_stage, delay_stage):
    """ Newport UTM100pp.1 stage, when plugged into ESP300"""

    # this stage doesn't seem to work well with the ESP300.
    # better to use the old short_stage class

    _one_mm = 1 # = 1mm in stage units

    def initialize(self):
        mm = 2 # index for 'mm' label
        self.set_unit(mm)

        # thread pitch: 2 mm
        # gear reduction: 10 : 1
        # 2mm / 10 = 0.2 mm
        self.step_size = .2
        
        # encoder: 2000 ticks/rev at motor
        # 0.2 mm / 2000 = 0.1 um resolution
        self.encoder_resolution = 0.0001 # mm

        # max velocity, a glacial 2 mm/sec
        self.set_max_velocity(2)
        self.set_velocity(1.5) # faster?


class long_stage(ESP300_stage, delay_stage):
    _one_mm = 1 # = 1mm in stage units
    stage_length = 600 # mm
    c = 0.3 # mm / ps

class short_stage(MM3000_stage, delay_stage):
    _one_mm = 1e4 # = 1mm in stage units
    mm = 1e4
    stage_length = 100 * mm 
    c = 0.3 * mm #/ ps

       
