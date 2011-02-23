# this module contains methods to operate
# the agilent 8648A RF signal generator
# which runs on GPIB address 18
#
# tkb

import visa
from time import sleep

class ag8648(object):
    """
    The Agilent 8648A/B/C/D RF signal generator.

    We have one on our GPIB network at address 18.
    This is the factory-set default.

    >>> rf = ag8648("GPIB::18")

    Attributes:

        on -- boolean indicating whether RF
              output is on or off.
        amp -- RF output amplitude, in DBM.

    The signal generator can be controlled remotely 
    by setting these attributes of the instance.

    """

    def __init__(self, addr='GPIB::18'):
        self.bus = visa.instrument(addr)

    @property
    def on(self):
        resp  = self.bus.ask("OUTP:STAT?")
        return bool(int(resp))

    @on.setter
    def on(self, val):
        if val:
            cmd = "ON"
        else:
            cmd = "OFF"
        self.bus.write("OUTP:STAT %s" % cmd)

    @property
    def amp(self):
        resp  = self.bus.ask("POW:AMPL?")
        return float(resp)

    @amp.setter
    def amp(self, val, unit="DBM"):
        """
        Set the output amplitude. Assumes units of DBM.

        Available units: DBM, MV, UV,
        MVEMF, UVEMF, DBUV, DBUVEMF.

        """
        cmd = "POW:AMPL %.1f %s" % (val,unit)
        self.bus.write(cmd)

    @property
    def freq(self):
        """ Return the RF frequency in MHz.  """
        resp  = self.bus.ask("FREQ:CW?")
        return float(resp) / 10**6

    @freq.setter
    def freq(self, val, unit="MHZ"):
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

    def blink(self, interval = 1.):
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





