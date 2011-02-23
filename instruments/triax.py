# a library to talk to the Triax spectrometer
# which runs on address 1 of the GPIB network
#
# tkb

from visa import instrument, VisaIOError
from time import sleep


class triax(object):
    def __init__(self,addr='GPIB::1'):
        self.bus = instrument(addr)
        self.bus.timeout = 20
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
        try:
            response = self.bus.ask("E")
        except VisaIOError:
            print "VISA operation timed out"
            return True
        if response[0] != 'o':
            print "triax in trouble! %s" % response
        return self.busyCodes[response[1:]]

    def get_wavelength(self):
        """query the current wavelength"""
        response = self.bus.ask("Z62,1")
        return float(response[1:])

    def set_wavelength(self,wavelength):
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
                raise Exception("triax still frozen after %.2f sec")
        self.freeze_counter = 0

    wavelength = property(get_wavelength,set_wavelength)
    wl = wavelength


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
