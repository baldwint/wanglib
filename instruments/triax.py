"""
a library to talk to the Triax spectrometer
which runs on address 1 of the GPIB network

"""

#from visa import instrument, VisaIOError
#from visa import VisaIOError
from wanglib.util import Gpib, InstrumentError
from time import sleep


class triax(object):
    """
    A Jobin-Yvon "triax" spectrometer.

    Typically controlled over GPIB, address 1. Alternately,
    pass a bus object to the constructor.

    """
    def __init__(self, bus=None):
        if bus is not None:
            self.bus = bus
        else:
            self.bus = Gpib(0, 1)
#        self.bus.timeout = 20
        self.freeze_counter = 0
        self.freeze_tol = 2
        # extension: verify that the instrument
        # is at the given address

    busyCodes = {"q": True,
                 "": True,
                 "z": False }

    check_interval = 0.050

    def is_busy(self):
        """ ask the Triax if its motors are busy """
#        try:
#            response = self.bus.ask("E")
#        except VisaIOError:
#            print "VISA operation timed out"
#            return True
        response = self.bus.ask("E")
        if response[0] != 'o':
            print "triax in trouble! %s" % response
        return self.busyCodes[response[1:]]

    @property
    def wavelength(self):
        """query the current wavelength"""
        response = self.bus.ask("Z62,1")
        return float(response[1:])
    @wavelength.setter
    def wavelength(self,wavelength):
        """move to a new wavelength"""
        command = "Z61,1,"+str(wavelength)
        response = self.bus.ask(command)
        # even though this is a write-only command,
        # triax still returns 'o' for okay
        sleep(self.check_interval)
        while self.is_busy():
            # wait for the motors to rest
            sleep(self.check_interval)
            self.freeze_counter += self.check_interval
            if self.freeze_counter >= self.freeze_tol:
                raise InstrumentError("triax still frozen after %.2f sec")
        self.freeze_counter = 0

    # shortcut for lazy typists
    wl = wavelength

    def initialize(self):
        """
        Perform the power-up routine.

        This should take two minutes.

        """
        self.bus.write("A")
        print "init started, waiting 2 minutes"
        sleep(120)
#        # set entrance slits
#        self.bus.write("i0,0,0\r")
#        sleep(0.5)
#        # set exit slits to zero
#        self.bus.write("i0,0,0\r")
#        sleep(0.5)
        # get status
        resp = self.bus.read()
        return resp



if __name__ == "__main__":
    from sys import argv
    spec = triax()
    spec.wavelength = argv[1]

    while spec.wavelength <= 815:    
        spec.wavelength = spec.wavelength + 1
        while spec.busy:
            print spec.wavelength
            sleep(0.1)
        print "made it to %.4f" % spec.wavelength    
    print "all done!"
    print spec.wavelength
