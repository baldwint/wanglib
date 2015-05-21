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
        self.query() # this switches it to query mode
        self.purge()

    def __del__(self):
        self.bus.close()

    def query(self):
        """
        Request a single response string.

        The first time the wavemeter receives this command,
        it will switch from broadcast to query mode.
        """
        self.bus.write('@\x51\r\n')
        response = self.bus.read(23)
        return response

    def purge(self):
        """ purge the buffer of old measurements"""
        while self.bus.inWaiting() > 0:
            self.bus.read(self.bus.inWaiting())

    def parse(self, response):
        """ parse the wavemeter's broadcast string """
        # this is documented on page 30 of the manual
        meas, display, system = response.split(',')
        if 'LO SIG' in meas:
            approx = True
            val = None
        elif meas[0] == '~':
            approx = True
            val = float(meas[1:])
        elif meas[0] == '+':
            approx = False
            val = float(meas)
        elif meas[0] == '-':
            approx = False
            val = float(meas)
        else:
            raise ValueError('unknown response ' + meas)
        return approx, val, int(display, 16), int(system, 16)

    def get_response(self):
        response = self.query()
        return self.parse(response)

    def get_wl(self):
        """ Get the current wavelength (or frequency) """
        ax, wl, ds, ss = self.get_response()
        return wl
    wl = property(get_wl)
    """ Current wavelength (or frequency) """

    def get_unit(self):
        ax, wl, ds, ss = self.get_response()
        return self.parse_code(ds, self.unit_masks)
    unit = property(get_unit)

    def get_display(self):
        ax, wl, ds, ss = self.get_response()
        return self.parse_code(ds, self.display_masks)
    display = property(get_display)

