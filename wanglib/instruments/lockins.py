#!/usr/bin/env python

"""
Lock-in amplifiers are commonly used for sensitive detection of a
modulated voltage signal. They enable us to measure both the amplitude
and phase of a signal, which we can access in either the cartesian (X,
Y) or polar (R, phase) basis.

This module provides interfaces to two brands of lock-in, using two
corresponding classes.

    :EG&G 5110:      :class:`wanglib.instruments.lockins.egg5110`
    :SRS 830:        :class:`wanglib.instruments.lockins.srs830`

.. note::
    The methods implemented by these two classes are named the same, but
    don't always behave the same way. For example, the EG&G 5110
    returns a 2-tuple with unit when the ADC ports are queried, but
    the SRS 830 always returns a figure in volts.

.. warning::
    I'm working toward parity between the return value formats of the
    two classes. This will make it easier to switch between lock-ins,
    but will break existing code!

"""

from wanglib.util import InstrumentError, sciround

class srs830(object):
    """ A Stanford Research Systems model SR830 DSP lock-in.

    Typically controlled over GPIB, address 8. Instantiate like:

    >>> li = srs830(plx.instrument(8))

    where ``plx`` is a prologix controller.
    pyVISA instruments should also work fine.

    """

    def __init__(self, bus):
        self.bus = bus

    ADC_cmd = "OAUX?%d"
    ADC_range = (1, 2, 3, 4)

    measurements = {
        'X': 1,
        'Y': 2,
        'MAG': 3,
        'R': 3,
    }

    def measure(self, command):
        """
        Measure one of the usual signals (X, Y, or MAG).
        
        Results are given in units of volts or degrees.

        """
        #TODO: parity with the other lockin re: units
        cmd = 'OUTP?%d' % self.measurements[command]
        response = self.bus.ask(cmd)
        return float(response)

    def get_x(self):
        return self.measure('X')
    x = property(get_x)

    def get_y(self):
        return self.measure('Y')
    y = property(get_y)

    def get_r(self):
        return self.measure('MAG')
    r = property(get_r)

    def get_ADC(self,n):
        """ read one of the ADC ports. Return value in volts."""
        if n not in self.ADC_range:
            err = "Indicate ADC in range %s" % (self.ADC_range) 
            raise InstrumentError(err)
        response = self.bus.ask(self.ADC_cmd % n)
        return float(response)


class egg5110(object):
    """ An EG&G model 5110 lock-in.

    Typically controlled over GPIB, address 12. Instantiate like:

    >>> li = egg5110(plx.instrument(12))

    where ``plx`` is a prologix controller.
    pyVISA instruments should also work fine.

    """
    def __init__(self, bus):
        self.bus = bus

        # verify lockin identity
        resp = self.bus.ask("ID")
        if resp != '5110':    
            raise InstrumentError('5110 lockin not found')

    # sensitivity functions
    
    sensitivities = {0: (100,'nV'), \
                     1: (200,'nV'), \
                     2: (500,'nV'), \
                     3: (1,'uV'), \
                     4: (2,'uV'), \
                     5: (5,'uV'), \
                     6: (10,'uV'), \
                     7: (20,'uV'), \
                     8: (50,'uV'), \
                     9: (100,'uV'), \
                     10: (200,'uV'), \
                     11: (500,'uV'), \
                     12: (1,'mV'), \
                     13: (2,'mV'), \
                     14: (5,'mV'), \
                     15: (10,'mV'), \
                     16: (20,'mV'), \
                     17: (50,'mV'), \
                     18: (100,'mV'), \
                     19: (200,'mV'), \
                     20: (500,'mV'), \
                     21: (1,'V')}

    _V_scales = {'V': 1.,
                'mV': 1e-3,
                'uV': 1e-6,
                'nV': 1e-9}
    
    def get_sensitivity(self, unit='V'):
        """
        Get the current sensitivity, in Volts.

        >>> li.get_sensitivity()
        0.1

        If the `unit` kwarg is specified, the value will
        be converted to the desired unit instead.

        >>> li.get_sensitivity(unit='uV')
        100000.

        Using `unit=True` will return a value in a 2-tuple
        along with the most sensible unit (as a string).

        >>> li.get_sensitivity(unit=True)
        (100, 'mV')

        """
        val = self.bus.ask("SEN")
        q,u = self.sensitivities[int(val)]
        if unit in self._V_scales.keys():
            sens = q * self._V_scales[u] / self._V_scales[unit]
            return sciround(sens, 1)
        else:
            return q,u
    def set_sensitivity(self,code):
        """Set the current sensitivity (Using a code)."""
        self.bus.write("SEN %d" % code)
    sensitivity = property(get_sensitivity,set_sensitivity)
    """ Current value of the sensitivity, in volts. """
    #TODO: set with a value in volts

    # time constant functions

    timeconsts = {0: (0,'MIN'), \
                  1: (1,'ms'), \
                  2: (3,'ms'), \
                  3: (10,'ms'), \
                  4: (30,'ms'), \
                  5: (100,'ms'), \
                  6: (300,'ms'), \
                  7: (1,'s'), \
                  8: (3,'s'), \
                  9: (10,'s'), \
                  10: (30,'s'), \
                  11: (100,'s'), \
                  12: (300,'s')}

    def get_timeconst(self):
        """Get the current time constant (as a 2-tuple)."""
        val = self.bus.ask("TC")
        return self.timeconsts[int(val)]
    def set_timeconst(self,code):
        """Set the current time constant (Using a code)."""
        self.bus.write("TC %d" % code)
    timeconst = property(get_timeconst,set_timeconst)
    """
    Current value of the time constant as a 2-tuple.

    """

    # measurement functions

    def measure(self, command, unit='V'):
        """
        Measure one of the usual voltage signals (X, Y, or MAG).

        >>> li.measure('X')
        0.0014
        
        Results are given in volts. To specify a different
        unit, use the ``unit`` kwarg.

        >>> li.measure('X', unit='mV')
        1.4

        To skip this conversion, and instead return the
        result as a fraction of the sensitivity (what the
        manual calls "percent of full-scale"), specify
        ``unit=None``:

        >>> li.measure('X', unit=None)
        .14

        You will need to multiply by the sensitivity (in
        this example, 10mV) to get a meaningful number.
        To perform this multiplication automatically,
        specify ``unit=True``:

        >>> li.measure('X', unit=True)
        (1.4, 'mV')

        This returns a 2-tuple containing the measurement
        and the unit string ("V", "mV", etc.),

        .. note ::
            to provide an answer in real units, the EG&G
            5110 needs to be queried for its sensitivity
            on every single measurement. This can slow
            things down. If you need to make measurements
            quickly, and are using a fixed sensitivity,
            specify ``unit=None`` for speed.

        """
        response = self.bus.ask(command)
        # the 5110 lockin returns measurements
        # as ten-thousandths of full-scale
        fraction = int(response) / 10000.
        if unit is None:
            return fraction 
        elif unit in self._V_scales.keys():
            sens = self.get_sensitivity(unit=unit)
            return fraction * sens
        else:
            sens,unit = self.get_sensitivity(unit=True)
            return fraction * sens, unit

    def get_x(self):
        """ Get current value of X, in volts. """
        return self.measure('X')
    x = property(get_x)
    """Current value of X, in volts. """

    def get_y(self):
        """ Get current value of Y, in volts. """
        return self.measure('Y')
    y = property(get_y)
    """Current value of Y, in volts. """

    def get_r(self):
        """ Get current value of R, in volts. """
        return self.measure('MAG')
    r = property(get_r)
    """Current value of R, in volts. """

    def get_phase(self):
        """ Get current value of the phase, in degrees. """
        # phase measurements come in millidegrees
        # so convert them to degrees
        multiplier = float(1) / 1000
        response = self.bus.ask('PHA')
        return int(response) * multiplier
    phase = property(get_phase)
    """Current value of the phase, in degrees. """

    # adc function

    def get_ADC(self,n):
        """Read one of the four ADC ports. Return value in volts."""
        if n not in range(1,4):
            raise InstrumentError("Indicate ADC between 1 and 4")
        response = self.bus.ask("ADC %d" % n)
        return 0.001 * int(response)

    def autophase(self):
        """ 
        Automatically adjust the reference phase
        to maximize the X signal and minimize Y.

        """
        self.bus.write("AQN")

    @property
    def lights(self):
        """ Boolean. Turns the front panel lights on or off. """
        response = self.bus.ask("LTS")
        return bool(int(response))

    @lights.setter
    def lights(self, arg):
        cmd = "LTS %d" % bool(arg)
        self.bus.write(cmd)

