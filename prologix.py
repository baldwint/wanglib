from wanglib.util import Serial
from time import sleep, time

class prologix_USB(object):
    """
    Interface to a prologix usb-gpib controller.

    """

    def __init__(self, port='/dev/ttyUSBgpib'):
        # open log file
        self.lf = open('prologix.log', 'a')
        self.start = time()
        self.lf.write('\nplx initialized at %.2f\n\n' % self.start)

        # create a serial port object
        self.bus = Serial(port, baudrate=115200, rtscts=1, log='plx.log')
        # if this doesn't work, try settin rtscts=0

        # flush whatever is hanging out in the buffer
        self.bus.readall()
        # don't save settings (to avoid wearing out EEPROM)
        self.savecfg = False

        # keep a local copy of the current address
        # so we're not always asking for it
        self._addr = self.addr

    def clock(self):
        return time() - self.start

    def write(self, command, lag=0.5):
        self.bus.write("%s\r" % command)
        self.lf.write('%.2f write: %s\n' % (self.clock(), command))
        sleep(lag)

    def readall(self):
        resp = self.bus.readall()
        self.lf.write('%.2f read: ' % self.clock())
        self.lf.write(resp)
        return resp.rstrip()

    def ask(self, query, *args, **kwargs):
        """ Write to the bus, then read response. """
        self.readall()  # clear the buffer
        self.write(query, *args, **kwargs)
        return self.readall()

    # use addr to select an instrument by its GPIB address

    @property
    def addr(self):
        """ which GPIB address is currently selected? """
        # query the controller for the current address
        # and save it in the _addr variable (why not)
        self._addr = int(self.ask("++addr"))
        return self._addr
    @addr.setter
    def addr(self, new_addr):
        # change to the new address
        self.write("++addr %d" % new_addr)
        # update local record
        self._addr = new_addr

    # settings specific to the Prologix controller

    def version(self):
        """ Query the Prologix firmware version """
        return self.ask("++ver")

    @property
    def savecfg(self):
        resp = self.ask("++savecfg")
        return bool(int(resp))
    @savecfg.setter
    def savecfg(self, val):
        d = bool(val)
        self.write("++savecfg %d" % d)





class instrument(object):
    """
    Represents an instrument attached to
    a Prologix controller.

    Pass the controller instance and GPIB address
    to the constructor. This creates a GPIB instrument
    at address 12:

    >>> plx = prologix_USB()
    >>> inst = instrument(plx, 12)

    Then use the ask() and write() methods to
    send gpib queries and commands.

    """

    def __init__(self, controller, addr):
        self.addr = addr
        self.controller = controller

    def get_priority(self):
        """
        switch the controller address to the
        address of this instrument

        """
        if self.addr != self.controller._addr:
            self.controller.addr = self.addr

    def ask(self, command):
        self.get_priority()
        return self.controller.ask(command)

    def read(self): # behaves like readall
        self.get_priority()
        return self.controller.readall()

    def write(self, command):
        self.get_priority()
        self.controller.write(command)

