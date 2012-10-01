#!/usr/bin/env python
"""
Interfaces to Tektronix oscilloscopes.

"""

from wanglib.util import InstrumentError, sciround
import numpy

class TDS3000(object):
    """ A Tektronix oscilloscope from the TDS3000 series.

    Can be controlled over GPIB, RS-232, or Ethernet. Just
    pass an object with ``write``, ``read``, and ``ask`` methods
    to the constructor.

    >>> from wanglib.util import Serial
    >>> bus = Serial('/dev/ttyS0', rtscts=True)
    >>> scope = tds3000(bus)

    If using RS-232 (as above), be sure to use rtscts, and
    connect using a null modem cable.
    You will probably need to use the highest baud rate you can.

    """

    class _parameterset(dict):
        """ A set of single-value commands, as a dictionary. """

        def __init__(self, bus, prefix='',
                    strs = (), floats = (),
                     ints = (), bools = ()):
            self.bus = bus
            self.prefix = prefix
            self.strs = strs
            self.floats = floats
            self.ints = ints
            self.bools = bools

        def keys(self):
            return list(self.strs + self.floats +
                        self.ints + self.bools)

        def __getitem__(self, key):
            key = key.upper()
            result = self.bus.ask(
                '%s%s?' % (self.prefix, key)).rstrip()
            if key in self.strs:
                return result
            elif key in self.floats:
                return float(result)
            elif key in self.ints:
                return int(result)
            elif key in self.bools:
                return bool(int(result))
            else:
                raise NotImplementedError

        def __setitem__(self, key, value):
            key = key.upper()
            if key in self.strs:
                self.bus.write('%s%s %s' % (self.prefix, key, value))
            elif key in self.bools + self.ints:
                self.bus.write('%s%s %d' % (self.prefix, key, int(value)))
            else:
                raise NotImplementedError

    def __init__(self, bus=None):
        if bus is None:
            from wanglib.util import Serial
            bus = Serial('/dev/ttyS0', baudrate=19200,
                         rtscts=True, term_chars='\n')
        self.bus = bus
        self.wfmpre = self._parameterset(bus, prefix='WFMP:',
            strs = ('ENCDG', 'BN_FMT', 'BYT_OR', 'XUNIT', 'YUNIT'),
            floats = ('XZERO', 'XINCR', 'YOFF', 'YZERO', 'YMULT'),
            ints = ('BYT_NR', 'BIT_NR', 'NR_PT', 'PT_OFF'))
        self.acquire = self._parameterset(bus, prefix = 'ACQ:',
            strs = ('MODE', 'STOPA'),
            ints = ('NUMAVG', 'NUMENV'),
            bools = ('STATE',))

    acquire = dict()
    """
    Dictionary of acquisition parameters.

    :param MODE:   one of ``SAMple``, ``PEAKdetect``,
                          ``AVErage``, or ``ENVelope``.
    :type MODE:    string
    :param STOPA:  controls whether we are in "single sequence" mode -
                   that is, should data acquisition stop once the
                   acquisition mode has been satisfied (``SEQuence``),
                   or should it strictly be stopped and started by the
                   RUN/STOP button on the front panel (``RUNSTop``)?
    :type STOPA:   string
    :param STATE:  is data currently being acquired?
    :type STATE:   bool
    :param NUMAVG: when ``STATE`` is ``AVErage``, how big should the
                   basis be for the average?
                   One of 2, 4, 8, 16, 32, 64, 128, 256, or 512.
    :type NUMAVG:  int
    :param NUMENV: when ``STATE`` is ``ENVelope``, how big should the
                   basis be for the envelope?
                   One of 2, 4, 8, 16, 32, 64, 128, 256, 512, or 0
                   (for infinite enveloping).
    :type NUMENV:  int

    """
    def acquire_restart(self):
        """
        Discards collected data and restarts acquisition.

        """
        self.bus.write('ACQ:STATE RUN')

    #TODO document wfmpre parameter set

    @property
    def data_source(self):
        """
        Determines the default data curve returned by :meth:`get_curve`.

        Possible values include `CH1`, `CH2`, `CH3`, `CH4`,
        `MATH`, `MATH1` (same as `MATH`), `REF1`, `REF2`, `REF3`,
        and `REF4`.

        """
        result = self.bus.ask('DAT:SOU?')
        return result.rstrip()

    @data_source.setter
    def data_source(self, val):
        if type(val) is int:
            val = 'CH%d' % val
        result = self.bus.write('DAT:SOU %s' % val)

    def is_active(self, channel):
        """
        Ask whether a given waveform is active

        :param channel: `CH1`, `CH2`, `CH3`, `CH4`,
        `MATH`, `MATH1` (same as `MATH`), `REF1`, `REF2`, `REF3`,
        or `REF4`.

        """
        return bool(int(self.bus.ask('sel:%s?' % channel)))

    def get_curve(self, source=None):
        """
        Fetch a trace.

        :param source: Channel to retrieve. Defaults to
            value of :attr:`data_source`. Valid channels are
            `CH1`, `CH2`, `CH3`, `CH4`, `MATH`, `MATH1` (same as
            `MATH`), `REF1`, `REF2`, `REF3`, or `REF4`.
        :returns: A numpy array representing the current waveform.

        """
        if source is None:
            source = self.data_source
        else:
            self.data_source = source
        if not self.is_active(source):
            raise InstrumentError('%s not turned on' % source)

        fmt = '>' if self.wfmpre['BYT_OR'] == 'MSB' else '<'
        fmt += 'i' if self.wfmpre['BN_FMT'] == 'RI' else 'u'
        fmt += str(self.wfmpre['BYT_NR'])

        self.bus.write('CURV?')
        result = self.bus.read() # reads either everything (GPIB)
                                 # or a single byte (RS-232)
        if result == '#':
            meta_len = int(self.bus.read(1))
            data_len = int(self.bus.read(meta_len))
            result = self.bus.read(data_len)
            self.bus.read(1) # read final newline
        elif len(result) == 1:
            # if we received something other than a pound sign
            raise InstrumentError('Unknown first byte: %s' % result)

        return numpy.fromstring(result, dtype = fmt)

    def get_wfm(self, source=None):
        """
        Fetch a trace, scaled to actual units.

        :param source: Channel to retrieve. Defaults to
            value of :attr:`data_source`. Valid channels are
            `CH1`, `CH2`, `CH3`, `CH4`, `MATH`, `MATH1` (same as
            `MATH`), `REF1`, `REF2`, `REF3`, or `REF4`.
        :returns: Two numpy arrays: `t` and `y`

        """
        curv = self.get_curve(source).astype(float)
        y = ((curv - self.wfmpre['YOFF'])
             * self.wfmpre['YMULT']) + self.wfmpre['YZERO']
        t = (numpy.arange(self.wfmpre['NR_PT'], dtype=float)
             * self.wfmpre['XINCR']) + self.wfmpre['XZERO']
        return t, y

    def get_timediv(self):
        """
        Get time per division, in seconds.

        :returns: Seconds per division, as a floating-point number.
        """
        result = self.bus.ask('HOR:MAI:SCA?')
        return float(result.rstrip())

    _acceptable_timedivs = (  10,   4,    2,    1,
                                 4e-1, 2e-1, 1e-1,
                                 4e-2, 2e-2, 1e-2,
                                 4e-3, 2e-3, 1e-3,
                                 4e-4, 2e-4, 1e-4,
                                 4e-5, 2e-5, 1e-5,
                                 4e-6, 2e-6, 1e-6,
                                 4e-7, 2e-7, 1e-7,
                                 4e-8, 2e-8, 1e-8,
                                 4e-9, 2e-9, 1e-9)

    def set_timediv(self, to):
        """
        Set time per division, in seconds.

        :param to:  Desired seconds per division.
                    Acceptable values range from 10 seconds to 1, 2, or
                    4ns, depending on model, in a 1-2-4 sequence.
        :type to:   float

        """
        to = sciround(to, 1)
        if to in self._acceptable_timedivs:
            self.bus.write('HOR:MAI:SCA %.0E' % to)
        else:
            raise InstrumentError('Timediv not in %s' %
                                  str(self._acceptable_timedivs))

    timediv = property(get_timediv, set_timediv)
    """ Time per division, in seconds. """

if __name__ == "__main__":
    scope = TDS3000()

