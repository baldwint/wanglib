from wanglib.util import Serial
from socket import socket, AF_INET, SOCK_STREAM, IPPROTO_TCP
from time import sleep

class prologix_base(object):
    """
    Base class for prologix controllers (ethernet/usb)

    """

    def __init__(self):
        """
        initialization routines common to USB and ethernet

        """
        # keep a local copy of the current address
        # and read-after write setting
        # so we're not always asking for it
        self._addr = self.addr
        self._auto = self.auto


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
        # update local record
        self._addr = new_addr
        # change to the new address
        self.write("++addr %d" % new_addr)
        # we update the local variable first because the 'write'
        # command may have a built-in lag. if we intterupt a program
        # during this period, the local attribute will be wrong

    @property
    def auto(self):
        """
        should the controller automatically let instruments talk
        after writing to them? 

        """
        self._auto = bool(int(self.ask("++auto")))
        return self._auto
    @auto.setter
    def auto(self, val):
        self._auto = bool(val)
        self.write("++auto %d" % self._auto)

    def version(self):
        """ Query the Prologix firmware version """
        return self.ask("++ver")

    @property
    def savecfg(self):
        """ should the controller save settings in EEPROM?  """
        resp = self.ask("++savecfg")
        if resp == 'Unrecognized command':
            raise Exception("""
                Prologix controller does not support ++savecfg
                update firmware or risk wearing out EEPROM
                            """)
        return bool(int(resp))
    @savecfg.setter
    def savecfg(self, val):
        d = bool(val)
        self.write("++savecfg %d" % d)

    def instrument(self, addr, **kwargs):
        """
        factory function for instrument objects.

        addr -- the GPIB address for an instrument
                attached to this controller.
        """
        return instrument(self, addr, **kwargs)


class prologix_ethernet(prologix_base):
    """
    Interface to a prologix gpib-ethernet controller.

    """

    def __init__(self, ip='128.223.131.156'):
        # open a socket to the controller
        self.bus = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP)
        self.bus.settimeout(5)
        self.bus.connect((ip, 1234))

        # change to controller mode
        self.bus.send('++mode 1\n')

        # do common startup routines
        super(prologix_ethernet, self).__init__()

    def write(self, command, lag=0.1):
        self.bus.send("%s\n" % command)
        sleep(lag)

    def readall(self):
        resp = self.bus.recv(100) #100 should be enough, right?
        return resp.rstrip()

    def ask(self, query, *args, **kwargs):
        """ Write to the bus, then read response. """
        # no need to clear buffer
        self.write(query, *args, **kwargs)
        return self.readall()


class prologix_USB(prologix_base):
    """
    Interface to a prologix usb-gpib controller.

    """

    def __init__(self, port='/dev/ttyUSBgpib', log=False):
        # create a serial port object
        self.bus = Serial(port, baudrate=115200, rtscts=1, log=log)
        # if this doesn't work, try settin rtscts=0

        # flush whatever is hanging out in the buffer
        self.bus.readall()

        # don't save settings (to avoid wearing out EEPROM)
        self.savecfg = False

        # do common startup routines
        super(prologix_USB, self).__init__()

    def write(self, command, lag=0.1):
        self.bus.write("%s\r" % command)
        sleep(lag)

    def readall(self):
        resp = self.bus.readall()
        return resp.rstrip()

    def ask(self, query, *args, **kwargs):
        """ Write to the bus, then read response. """
        self.bus.log_something('note', 'clearing buffer - expect no result')
        self.readall()  # clear the buffer
        self.write(query, *args, **kwargs)
        return self.readall()

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

    def __init__(self, controller, addr,
                 delay=0.1, auto=True):
        """
        Constructor method for instrument objects.

        required arguments:
            controller -- the prologix controller instance
                to which this instrument is attached.
            addr -- the address of the instrument
                on controller's GPIB bus.

        keyword arguments:
            delay -- seconds to wait after each write.
            auto -- read-after-write setting.

        """
        self.addr = addr
        self.auto = auto
        self.delay = delay
        self.controller = controller

    def get_priority(self):
        """
        configure the controller to address this instrument

        """
        # configure instrument-specific settings
        if self.auto != self.controller._auto:
            self.controller.auto = self.auto
        # switch the controller address to the
        # address of this instrument
        if self.addr != self.controller._addr:
            self.controller.addr = self.addr

    def ask(self, command):
        """ query the instrument.  """
        # clear stray bytes from the buffer.
        # hopefully, there will be none.
        # if there are, print a warning
#        clrd = self.controller.bus.inWaiting()
#        if clrd > 0:
#            print clrd, 'bytes cleared'
#        self.read()  # clear the buffer
        self.write(command)
        return self.read()

    def read(self): # behaves like readall
        """ read response from instrument.  """
        self.get_priority()
        if not self.auto:
            # explicitly tell instrument to talk.
            self.controller.write('++read eoi', lag=self.delay)
        return self.controller.readall()

    def write(self, command):
        self.get_priority()
        self.controller.write(command, lag=self.delay)

