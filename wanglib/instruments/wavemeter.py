from serial import Serial
from time import time
import sys

class burleigh(object):
    """
    encapsulates a burleigh wavemeter

    """

    unit_codes = { '2549': 'nm',
                   '2552': 'cm-1',
                   '2564': 'GHz',
                   '2589': 'nm deviation',
                   '2592': 'cm-1 deviation',
                   '25A4': 'GHz deviation',
                 }

    def __init__(self, port = '/dev/ttyUSB0'):
        self.bus = Serial(port)

    def purge(self):
        """ purge the buffer of old measurements"""
        while self.bus.inWaiting() > 0:
            self.bus.read(self.bus.inWaiting())

    def parse(self, response):
        """ parse the wavemeter's broadcast string """
        meas, code, unknown = response.split(',')
        try:
            val = float(meas)
        except ValueError:
            val = None
        return val, self.unit_codes[code]

    def data_stream(self):
        start = time()
        self.purge() # purge the buffer
        while True:
            response = self.bus.readline().rstrip()
            sys.stdout.write('\r' + response)
            sys.stdout.flush()
            wl, unit = self.parse(response)
            yield time() - start, wl

    def get_wl(self):
        """ Get the current wavelength (or frequency) """
        self.purge() # purge the buffer
        response = self.bus.readline().rstrip()
        wl, unit = self.parse(response)
        return wl
    wl = property(get_wl)
    """ Current wavelength (or frequency) """

if __name__ == '__main__':
    from pylab import *
    from wanglib.pylab_extensions import plotgen
    ion()
    wm = burleigh()
    try:
        plotgen(wm.data_stream)
    except KeyboardInterrupt:
        show()
