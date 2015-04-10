from serial import Serial
from time import time
import sys

class burleigh(object):
    """
    encapsulates a burleigh wavemeter

    """

    # masks are given in appendix b, page 50 of the manual
    unit_masks = { 0x0009: 'nm',
                   0x0012: 'cm-1',
                   0x0024: 'GHz', }

    display_masks = { 0x0040: 'wavelength',
                      0x0080: 'deviation', }

    def parse_code(self, code, dic):
        mask = 0
        for k in dic:
             mask = mask | k
        result = code & mask
        return dic[result]

    def __init__(self, port = '/dev/ttyUSB0'):
        self.bus = Serial(port)

    def __del__(self):
        self.bus.close()

    def purge(self):
        """ purge the buffer of old measurements"""
        while self.bus.inWaiting() > 0:
            self.bus.read(self.bus.inWaiting())

    def parse(self, response):
        """ parse the wavemeter's broadcast string """
        # this is documented on page 30 of the manual
        meas, display, system = response.split(',')
        try:
            val = float(meas)
        except ValueError:
            val = None
        return val, int(display, 16), int(system, 16)

    def data_stream(self):
        start = time()
        self.purge() # purge the buffer
        while True:
            response = self.bus.readline().rstrip()
            sys.stdout.write('\r' + response)
            sys.stdout.flush()
            wl, ds, ss = self.parse(response)
            yield time() - start, wl

    def get_wl(self):
        """ Get the current wavelength (or frequency) """
        self.purge() # purge the buffer
        response = self.bus.readline().rstrip()
        wl, ds, ss = self.parse(response)
        return wl
    wl = property(get_wl)
    """ Current wavelength (or frequency) """

    def get_unit(self):
        self.purge() # purge the buffer
        response = self.bus.readline().rstrip()
        wl, ds, ss = self.parse(response)
        return self.parse_code(ds, self.unit_masks)
    unit = property(get_unit)

    def get_display(self):
        self.purge() # purge the buffer
        response = self.bus.readline().rstrip()
        wl, ds, ss = self.parse(response)
        return self.parse_code(ds, self.display_masks)
    display = property(get_display)

if __name__ == '__main__':
    from pylab import *
    from wanglib.pylab_extensions import plotgen
    ion()
    wm = burleigh()
    try:
        plotgen(wm.data_stream)
    except KeyboardInterrupt:
        show()
