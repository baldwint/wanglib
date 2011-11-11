#!/usr/bin/env python

"""
Interfaces to lock-in amplifiers.

"""

from wanglib.util import InstrumentError

class srs830(object):
    """ A Stanford Research Systems model SR830 DSP lock-in.

    Typically controlled over GPIB, address 8. Instantiate like:

    >>> li = srs830(plx.instrument(8))

    where plx is a prologix controller.
    pyVISA instruments should also work fine.

    So far, this class only implements the ADC functionality.

    """

    def __init__(self, bus):
        self.bus = bus

    ADC_cmd = "OAUX?%d"
    ADC_range = (1, 2, 3, 4)

    def getADC(self,n):
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

    where plx is a prologix controller.
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
    
    def getSensitivity(self):
        val = self.bus.ask("SEN")
        return self.sensitivities[int(val)]
    def setSensitivity(self,code):
        self.bus.write("SEN %d" % code)
    sensitivity = property(getSensitivity,setSensitivity)

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

    def getTimeconst(self):
        val = self.bus.ask("TC")
        return self.timeconsts[int(val)]
    def setTimeconst(self,code):
        self.bus.write("TC %d" % code)
    timeconst = property(getTimeconst,setTimeconst)

    # measurement functions

    def measure(self, command, unit=None):
        """
        Measure one of the usual signals (X, Y, or MAG).
        
        Results are given as a fraction of full-scale
        (that is, sensitivity). To change this behavior,
        use the 'unit' keyword argument.

        >>> li.measure('X', unit=True)

        This will return a 2-tuple containing the measurement
        and the unit string ("V", "mV", etc.),

        """
        response = self.bus.ask(command)
        # the 5110 lockin returns measurements
        # as ten-thousandths of full-scale
        fraction = int(response) / 10000.
        if unit is None:
            return fraction 
        else:
            sens,unit = self.sensitivity
            return fraction * sens, unit

    @property
    def x(self):
        return self.measure('X')
    @property
    def y(self):
        return self.measure('Y')
    @property
    def r(self):
        return self.measure('MAG')

    def getPhase(self):
        # phase measurements come in millidegrees
        # so convert them to degrees
        multiplier = float(1) / 1000
        response = self.bus.ask('PHA')
        return int(response) * mulitplier, 'degrees'
    phase = property(getPhase)

    # adc function

    def getADC(self,n):
        # read one of the four ADC ports
        if n not in range(1,4):
            raise InstrumentError("Indicate ADC between 1 and 4")
        response = self.bus.ask("ADC %d" % n)
        return 0.001 * response, 'V'

    def autophase(self):
        """ 
        Automatically adjust the reference phase
        to maximize the X signal and minimize Y.

        """
        self.bus.write("AQN")

    @property
    def lights(self):
        response = self.bus.ask("LTS")
        return bool(int(response))

    @lights.setter
    def lights(self, arg):
        cmd = "LTS %d" % bool(arg)
        self.bus.write(cmd)

