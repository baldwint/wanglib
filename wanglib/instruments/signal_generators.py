#!/usr/bin/env python

"""
Interfaces to Agilent RF signal generators.

"""

from time import sleep

class ag8648(object):
    """
    The Agilent 8648A/B/C/D RF signal generator.

    These instruments are configured to work on GPIB address 18
    by factory default. To instantiate one plugged in to prologix
    controller plx, do this:

    >>> rf = ag8648(plx.instrument(18))

    Other instrument objects (e.g. pyVISA) should also work.

    Attributes:

        on -- boolean indicating whether RF
              output is on or off.
        amp -- RF output amplitude, in DBM.

    The signal generator can be controlled remotely 
    by setting these attributes of the instance.

    >>> rf.amp
    -5.0
    >>> rf.amp = -10
    >>> rf.amp
    -10.0

    """

#    You can also use linux-gpib, if you use the wanglib version of the Gpib
#    driver. this class emulates the pyVISA interface.
#    For example, here's one at gpib address 19:
#
#    >>> from wanglib.util import Gpib
#    >>> rf = ag8648(Gpib(0, 19))
#

    def __init__(self, bus):
        self.bus = bus
        #TODO: verify connection

    def get_on(self):
        """ is RF output on? """
        resp  = self.bus.ask("OUTP:STAT?")
        return bool(int(resp))

    def set_on(self, val):
        if val:
            cmd = "ON"
        else:
            cmd = "OFF"
        self.bus.write("OUTP:STAT %s" % cmd)

    on = property(get_on, set_on)

    def get_pulse(self):
        """ is pulse modulation enabled? """
        resp  = self.bus.ask("PULM:STAT?")
        return bool(int(resp))

    def set_pulse(self, val):
        if val:
            cmd = "ON"
        else:
            cmd = "OFF"
        self.bus.write("PULM:STAT %s" % cmd)

    pulse = property(get_pulse, set_pulse)

    def get_amp(self):
        """ RF amplitude in dBm.  """
        resp  = self.bus.ask("POW:AMPL?")
        return float(resp)

    def set_amp(self, val, unit="DBM"):
        """
        Set the output amplitude. Assumes units of DBM.

        Available units: DBM, MV, UV,
        MVEMF, UVEMF, DBUV, DBUVEMF.

        """
        cmd = "POW:AMPL %.1f %s" % (val,unit)
        self.bus.write(cmd)

    amp = property(get_amp, set_amp)

    def get_freq(self):
        """ RF frequency in MHz.  """
        resp  = self.bus.ask("FREQ:CW?")
        return float(resp) / 10**6

    def set_freq(self, val, unit="MHZ"):
        """
        Set the RF frequency in MHz.

        """
        # maximum resolution:  10 Hz.
        fmt_vals = {
            "MHZ": "%.5f",
            "KHZ": "%.2f",
        }
        val = fmt_vals[unit] % val
        cmd = "FREQ:CW %s %s" % (val,unit)
        self.bus.write(cmd)

    freq = property(get_freq, set_freq)

    def blink(self, interval = 1.):
        """
        Blink the RF output on and off with time.

        Useful when aligning AOMs.

        """
        return_state = self.on
        while True:
            try:
                self.on = True
                sleep(interval / 2.)
                self.on = False
                sleep(interval / 2.)
            except KeyboardInterrupt:
                self.on = return_state
                break

