#!/usr/bin/env python

"""
Interfaces to New Focus diode laser controllers.

"""

from wanglib.util import InstrumentError, show_newlines

class velocity6300(object):
    """
    A New Focus Velocity 6300 diode laser controller.

    To instantiate, pass an instrument object to the constructor.
    e.g., for a controller with GPIB address 1, attached to a
    prologix GPIB controller:

    >>> laser = velocity6300(plx.instrument(1, auto=False))

    where ``plx`` is the prologix object. If you're using prologix,
    it's very important to turn off read-after-write!

    To use with RS232, use ``\\r`` as the termination
    character. For example:

    >>> from wanglib.util import Serial
    >>> laser = velocity6300(Serial('/dev/ttyUSB0', baudrate=19200, term_chars='\\r'))

    """

    # the 6300 has a non-standard GPIB implementation.
    # rather than render a response to each command sequentially
    # to the buffer and leaving it there until you read it,
    # this unit will respond to any read request
    # with the response to the most recent command - as many times
    # as you ask for it. This causes problems with prologix
    # GPIB controllers because it never appears to be done responding.
    # to avoid this, *always* turn off read-after-write using prologix.

    # furthermore, this controller responds to non-query commands
    # with the string 'OK'. We don't need to flush this out, though,
    # since that will be overwritten as soon as we issue a query.

    # use this behavior to make sensible error messages:
    def write(self, cmd):
        """
        Issue a command to the laser.

        This takes care of two things:
            - Formats the command with ``@`` if using RS-232
            - Verifies that the laser responds with ``OK``

        """
        # if communicating over serial, commands must start with '@'
        prepend = '@' if self.is_serial else ''
        resp = self.bus.ask(prepend + cmd).rstrip()
        if resp != 'OK':
            # try one more time
            resp = self.bus.ask(prepend + cmd)
        if resp != 'OK':
            msg = "laser didn't like command: %s. it says: %s"
            raise InstrumentError(msg % (cmd,resp))

    def __init__(self, bus):
        self.bus = bus
        # establish RS232 vs. GPIB by testing for 'isatty' method
        self.is_serial = hasattr(bus, 'isatty')
        print self.bus.ask('*IDN?')

    def stop_tracking(self):
        """ exit track mode to ready mode. """
        self.write('outp:trac off')

    @property
    def busy(self):
        """ is an operation in progress? """
        return not bool(int(self.bus.ask('*OPC?')))

    @property
    def on(self):
        """ is the laser on or off?"""
        return bool(int(self.bus.ask('outp?')))
    @on.setter
    def on(self, val):
        self.write('outp %d' % int(bool(val)))

    # ------------------
    # wavelength control
    # ------------------

    @property
    def wl(self):
        """ current wavelength of laser (nm) """
        return float(self.bus.ask('sens:wave'))
    @wl.setter
    def wl(self, val):
        # can take a numerical value, or 'min' or 'max'
        self.write('wave %s' % val)
#        self.stop_tracking()

#    @property
#    def wl_set(self):
#        """ wavelength set point """
#        return float(self.bus.ask('wave ?'))

# not sure what to do here just yet. should there be separate properties
# for the laser wavelength and its set-point? Also goes for piezo, etc.

# this is also a problem with my lockins, spectrometers, etc. I've been
# so property-happy that I've implemented some questionable functions
# as properties elsewhere in wanglib.

# for example, reading lockin measurements is done through a property,
# even though this isn't settable, and fluctuates. spectrometer wavelengths
# are settable, even though the value returned may be off a little bit.

# this may lead to errors in data if I'm not careful. time to change?

    @property
    def wl_min(self):
        """ min wavelength of this diode """
        return self.bus.ask('wave ? min')
    @property
    def wl_max(self):
        """ max wavelength of this diode """
        return self.bus.ask('wave ? max')

    @property
    def piezo(self):
        """ return piezo voltage as % of full-scale """
        return float(self.bus.ask('sens:volt:piez'))
    @piezo.setter
    def piezo(self, val):
        self.write('volt %s' % val)

    # ----------------------
    # other laser properties
    # ----------------------

    @property
    def power(self):
        """ return front-facet laser power level (mW)"""
        return float(self.bus.ask('sens:pow:fron'))

    @property
    def current(self):
        """ return current level in the diode (mA)"""
        return float(self.bus.ask('sens:curr:diod'))
    @current.setter
    def current(self, val):
        self.write('curr %s' % val)

